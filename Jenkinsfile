pipeline {
    // Configure this label only on a dedicated personal, local Docker agent.
    agent { label 'smartdesk-personal-local' }
    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
    }
    parameters {
        string(name: 'LOCAL_DOCKER_HOST', defaultValue: 'unix:///var/run/docker.sock',
               description: 'Explicit socket of a dedicated personal Docker daemon. Shared environments are not approved.')
    }
    environment {
        SMARTDESK_CI_DOCKER_HOST = "${params.LOCAL_DOCKER_HOST}"
        // Public checkout must not use ambient credential helpers or prompts.
        GIT_CONFIG_NOSYSTEM = '1'
        GIT_CONFIG_GLOBAL = '/dev/null'
        GIT_CONFIG_COUNT = '1'
        GIT_CONFIG_KEY_0 = 'credential.helper'
        GIT_CONFIG_VALUE_0 = ''
        GIT_TERMINAL_PROMPT = '0'
        GIT_ASKPASS = '/usr/bin/false'
        PYTHONDONTWRITEBYTECODE = '1'
    }
    stages {
        stage('Check out personal repository') {
            steps {
                script {
                    def remotes = scm.userRemoteConfigs
                    if (!remotes || remotes.any {
                        it.url != 'https://github.com/filipematos1982/smartdesk.git' || it.credentialsId
                    }) {
                        error('Use only the public personal SmartDesk SCM without credentials.')
                    }
                    checkout scm
                    env.CI_REPORT_ROOT = "reports/session4-ci-${env.BUILD_NUMBER}-${java.util.UUID.randomUUID()}"
                }
            }
        }
        stage('Build and validate local image with PostgreSQL') {
            steps {
                // A nonzero helper or pytest status fails this stage and the build.
                sh '''
                    set -eu
                    sh scripts/session4_ci.sh --approve-local-ci \
                        --docker-host "$SMARTDESK_CI_DOCKER_HOST" \
                        --output-dir "$CI_REPORT_ROOT"
                '''
            }
        }
    }
    post {
        always {
            script {
                if (env.CI_REPORT_ROOT) {
                    // Publish only this run's copied reports, never private lab state.
                    junit allowEmptyResults: false,
                          skipPublishingChecks: true,
                          testResults: "${env.CI_REPORT_ROOT}/artifacts/**/*.xml"
                    archiveArtifacts allowEmptyArchive: false,
                                     artifacts: "${env.CI_REPORT_ROOT}/artifacts/**",
                                     fingerprint: false
                }
            }
        }
    }
}
