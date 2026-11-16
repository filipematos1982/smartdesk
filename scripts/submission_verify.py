"""Verify an owned real loopback demo with synthetic data, then stop only that process."""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import subprocess
import sys
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]


def verify(output):
    output = Path(output).resolve()
    if output.parent != ROOT/'reports' or not re.fullmatch(r'submission-verification-[A-Za-z0-9_-]+', output.name):
        raise ValueError('Use a new reports/submission-verification-<unique-id> directory')
    os.umask(0o077)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    run = ROOT/'reports'/('submission-demo-qa-'+secrets.token_hex(8))
    env = {'PATH':'/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'}
    checks = []
    def check(name, result):
        checks.append({'name':name,'status':'passed' if result else 'failed'})
        if not result:
            raise AssertionError(name)
    process = None
    clients = []
    status = 'failed'
    reason = None
    with (output/'server.private.log').open('x') as log:
        try:
            process = subprocess.Popen([sys.executable,'-m','scripts.run_local_demo','--port','0','--output-dir',str(run)],
                                       cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
            manifest = None
            for _ in range(600):
                if process.poll() is not None:
                    raise RuntimeError('Owned demo exited before readiness')
                try:
                    manifest=json.loads((run/'manifest.json').read_text())
                except (OSError,json.JSONDecodeError):
                    pass
                if manifest and manifest['status']=='ready':
                    break
                time.sleep(.05)
            else:
                raise TimeoutError('Owned demo readiness timeout')
            check('owned_loopback_startup',manifest['pid']==process.pid and manifest['host']=='127.0.0.1'
                  and manifest['database_backend']=='sqlite' and manifest['synthetic_data_only'] is True)
            base='http://127.0.0.1:'+str(manifest['port'])
            accounts=json.loads((run/'accounts.private.json').read_text())
            by_email={account['email']:account for account in accounts}
            for _ in range(5):clients.append(httpx.Client(base_url=base,trust_env=False,timeout=10))
            anonymous,employee,other,technician,manager=clients
            def token(client):
                page=client.get('/login')
                return re.search(r'name="csrf-token" content="([^"]+)"',page.text).group(1)
            def post(client,path,data):
                return client.post(path,data=data,headers={'X-CSRF-Token':token(client)})
            def login(client,email):
                account=by_email[email]
                return post(client,'/login',{'email':email,'password':account['password']})
            check('live_health',anonymous.get('/health/live').json()=={'status':'live'})
            check('database_readiness',anonymous.get('/health/ready').json()=={'status':'ready'})
            check('anonymous_monitoring_denied',anonymous.get('/api/monitoring').status_code==401)
            check('missing_csrf_denied',anonymous.post('/login',data={'email':'employee@smartdesk.test','password':'synthetic'}).status_code==403)
            invalid=post(anonymous,'/login',{'email':'employee@smartdesk.test','password':'synthetic-invalid-password'})
            check('invalid_login_rejected',invalid.status_code==200 and 'Incorrect email or password' in invalid.text)
            for client,email in [(employee,'employee@smartdesk.test'),(other,'other@smartdesk.test'),
                                 (technician,'technician@smartdesk.test'),(manager,'manager@smartdesk.test')]:
                check('login_'+email.split('@')[0],login(client,email).status_code==303)
            advice=post(employee,'/api/assist/recommend',{'title':'Printer toner cartridge','description':'All users report printer outage'})
            check('local_advisory_recommendation',advice.status_code==200 and advice.json()['category']=='Hardware'
                  and advice.json()['priority']=='High' and advice.json()['provisional'] is True)
            check('technician_recommendation_denied',post(technician,'/api/assist/recommend',{'title':'Printer'}).status_code==403)
            with sqlite3.connect(str(run/'synthetic.sqlite3')) as db:
                check('advice_does_not_create_ticket',db.execute('SELECT count(*) FROM tickets').fetchone()[0]==0)
                tech_id=db.execute('SELECT id FROM users WHERE email=?',('technician@smartdesk.test',)).fetchone()[0]
            created=post(employee,'/tickets/new',{'title':'Submission synthetic ticket','description':'Printer paper jam','category':'Hardware'})
            check('ticket_creation',created.status_code==303)
            ticket_id=int(created.headers['location'].rsplit('/',1)[1])
            route='/api/tickets/'+str(ticket_id)
            check('other_employee_ticket',post(other,'/tickets/new',{'title':'Separate synthetic ticket','description':'Other data','category':'Software'}).status_code==303)
            check('employee_visibility_isolation','Separate synthetic ticket' not in employee.get('/tickets').text)
            check('technician_cannot_assign',post(technician,route+'/assign',{'technician_id':tech_id}).status_code==403)
            check('manager_assignment',post(manager,route+'/assign',{'technician_id':tech_id}).status_code==303)
            check('technician_start',post(technician,route+'/start',{}).status_code==303)
            check('technician_resolution',post(technician,route+'/resolve',{'resolution':'Synthetic repair'}).status_code==303)
            check('employee_reopen',post(employee,route+'/return',{}).status_code==303)
            check('technician_second_resolution',post(technician,route+'/resolve',{'resolution':'Synthetic verified repair'}).status_code==303)
            check('employee_cannot_close',post(employee,route+'/close',{'confirmed':'true'}).status_code==403)
            check('manager_close',post(manager,route+'/close',{'confirmed':'true'}).status_code==303)
            check('closed_ticket_cannot_reopen',post(employee,route+'/return',{}).status_code==400)
            with sqlite3.connect(str(run/'synthetic.sqlite3')) as db:
                check('fresh_sqlite_connection_persistence',db.execute('SELECT state FROM tickets WHERE id=?',(ticket_id,)).fetchone()[0]=='Closed')
            check('employee_monitoring_denied',employee.get('/api/monitoring').status_code==403)
            metrics=manager.get('/api/monitoring')
            check('manager_local_monitoring',metrics.status_code==200 and metrics.json()['counts']['authentication_failures']>=1
                  and metrics.json()['scope']=='single-process-local')
            check('logout',post(employee,'/logout',{}).status_code==303)
            check('logout_removes_monitoring_access',employee.get('/api/monitoring').status_code==401)
            status='passed'
        except Exception as exc:
            reason=type(exc).__name__
        finally:
            for client in clients:client.close()
            if process is not None and process.poll() is None:
                process.terminate()
                try:process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    status='failed';reason='Owned demo did not stop after SIGTERM'
    stopped=process is not None and process.poll() is not None
    if stopped and (run/'manifest.json').exists():
        stopped=json.loads((run/'manifest.json').read_text())['status']=='stopped'
    logs=(output/'server.private.log').read_text()
    credentials=json.loads((run/'accounts.private.json').read_text()) if (run/'accounts.private.json').exists() else []
    redacted=all(account['password'] not in logs for account in credentials)
    if not stopped or not redacted:status='failed'
    summary={'status':status,'checks':checks,'passed':sum(c['status']=='passed' for c in checks),
             'failed':sum(c['status']=='failed' for c in checks),'skipped':0,
             'owned_server_stopped':stopped,'passwords_absent_from_logs':redacted,
             'backend':'SQLite; not PostgreSQL','reason_type':reason,
             'private_demo_directory':str(run.relative_to(ROOT))}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    return 0 if status=='passed' else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approve-local-verification',action='store_true')
    parser.add_argument('--output-dir',required=True,type=Path)
    args=parser.parse_args()
    if not args.approve_local_verification:parser.error('Explicit synthetic local verification approval is required')
    return verify(args.output_dir)


if __name__=='__main__':raise SystemExit(main())
