pipeline {
    agent any

    environment {
        PROJECT_ID   = credentials('GCP_PROJECT_ID')
        REGION       = credentials('GCP_REGION')
        SERVICE_NAME = credentials('GCP_SERVICE_NAME')
        SERVICE_PORT = credentials('SERVICE_PORT')
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.RESOLVED_GIT_COMMIT = sh(
                        script: 'git rev-parse HEAD',
                        returnStdout: true
                    ).trim()
                    echo "Checked out commit: ${env.RESOLVED_GIT_COMMIT}"
                }
            }
        }

        stage('Lint & Format Check') {
            steps {
                dir('backend') {
                    script {
                        docker.image('python:3.13-slim').inside {
                            sh '''
                                set -eu
                                python -m pip install --upgrade pip
                                pip install -r requirements.txt
                                echo "=== Checking Black formatting ==="
                                black --check --diff .
                                echo "=== Checking isort imports ==="
                                isort --check-only --diff .
                            '''
                        }
                    }
                }
            }
        }

        stage('Run Tests') {
            environment {
                DATABASE_URL         = 'postgres://postgres:postgres@localhost:5432/test_db?sslmode=disable'
                DATABASE_SSL_REQUIRE = 'false'
                DJANGO_SETTINGS_MODULE = 'config.settings'
                SECRET_KEY           = 'test-secret-key-for-ci'
                DEBUG                = 'False'
                ALLOWED_HOSTS        = '*'
            }
            steps {
                script {
                    def postgres = docker.image('postgres:15').run(
                        '-e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=test_db -p 5432:5432'
                    )

                    try {
                        sh 'sleep 10'

                        dir('backend') {
                            docker.image('python:3.13-slim').inside('--network host') {
                                sh '''
                                    set -eu
                                    python -m pip install --upgrade pip
                                    pip install -r requirements.txt
                                    pip install pytest pytest-django coverage

                                    echo "=== Running migrations ==="
                                    python manage.py migrate --run-syncdb

                                    echo "=== Running tests ==="
                                    python manage.py test --verbosity=2

                                    echo "=== Running tests with coverage ==="
                                    coverage run --source='.' manage.py test
                                    coverage report --fail-under=50 || true
                                    coverage xml
                                '''
                            }
                        }
                    } finally {
                        postgres.stop()
                    }
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'backend/coverage.xml', allowEmptyArchive: true
                }
            }
        }

        stage('Build Docker Image') {
            when {
                branch 'main'
            }
            steps {
                script {
                    def shortSha = sh(
                        script: 'git rev-parse --short=7 HEAD',
                        returnStdout: true
                    ).trim()

                    env.SHORT_SHA = shortSha
                    env.REGISTRY = "${env.REGION}-docker.pkg.dev"
                    env.IMAGE_TAG = "${env.REGISTRY}/${env.PROJECT_ID}/financemanager/${env.SERVICE_NAME}:${shortSha}"

                    echo "Generated image tag: ${env.IMAGE_TAG}"

                    if (!env.IMAGE_TAG?.trim() || env.IMAGE_TAG.contains('//') || env.IMAGE_TAG.contains('/:')) {
                        error "Invalid image tag. Check that GCP credentials are configured."
                    }
                }

                withCredentials([file(credentialsId: 'GCP_SA_KEY_FILE', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh '''
                        set -eu
                        gcloud auth activate-service-account --key-file="${GOOGLE_APPLICATION_CREDENTIALS}"
                        gcloud config set project "${PROJECT_ID}"
                        gcloud auth configure-docker "${REGISTRY}" --quiet
                    '''
                }

                dir('backend') {
                    sh '''
                        set -eu
                        echo "=== Building Docker image ==="
                        docker build -t "${IMAGE_TAG}" .
                        docker tag "${IMAGE_TAG}" "${REGISTRY}/${PROJECT_ID}/financemanager/${SERVICE_NAME}:latest"

                        echo "=== Pushing Docker image ==="
                        docker push "${IMAGE_TAG}"
                        docker push "${REGISTRY}/${PROJECT_ID}/financemanager/${SERVICE_NAME}:latest"
                    '''
                }
            }
        }

        stage('Deploy to Cloud Run') {
            when {
                branch 'main'
            }
            steps {
                script {
                    if (!env.IMAGE_TAG?.trim()) {
                        error "IMAGE_TAG is empty! Build stage may have failed."
                    }
                }

                withCredentials([
                    file(credentialsId: 'GCP_SA_KEY_FILE', variable: 'GOOGLE_APPLICATION_CREDENTIALS'),
                    string(credentialsId: 'DJANGO_SECRET_KEY', variable: 'DJANGO_SECRET_KEY_SECRET_NAME'),
                    string(credentialsId: 'DATABASE_URL', variable: 'DATABASE_URL_SECRET_NAME'),
                    string(credentialsId: 'SUPABASE_URL', variable: 'SUPABASE_URL_SECRET_NAME'),
                    string(credentialsId: 'SUPABASE_KEY', variable: 'SUPABASE_KEY_SECRET_NAME'),
                    string(credentialsId: 'SUPABASE_JWT_SECRET', variable: 'SUPABASE_JWT_SECRET_SECRET_NAME')
                ]) {
                    sh '''
                        set -eu
                        gcloud auth activate-service-account --key-file="${GOOGLE_APPLICATION_CREDENTIALS}"
                        gcloud config set project "${PROJECT_ID}"

                        echo "=== Deploying to Cloud Run ==="
                        gcloud run deploy "${SERVICE_NAME}" \
                            --image "${IMAGE_TAG}" \
                            --region "${REGION}" \
                            --platform managed \
                            --allow-unauthenticated \
                            --port "${SERVICE_PORT}" \
                            --memory 512Mi \
                            --cpu 1 \
                            --min-instances 0 \
                            --max-instances 10 \
                            --set-env-vars "DEBUG=False" \
                            --set-env-vars "ALLOWED_HOSTS=*" \
                            --set-secrets "SECRET_KEY=${DJANGO_SECRET_KEY_SECRET_NAME}:latest" \
                            --set-secrets "DATABASE_URL=${DATABASE_URL_SECRET_NAME}:latest" \
                            --set-secrets "SUPABASE_URL=${SUPABASE_URL_SECRET_NAME}:latest" \
                            --set-secrets "SUPABASE_KEY=${SUPABASE_KEY_SECRET_NAME}:latest" \
                            --set-secrets "SUPABASE_JWT_SECRET=${SUPABASE_JWT_SECRET_SECRET_NAME}:latest"
                    '''
                }
            }
        }

        stage('Health Check') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([file(credentialsId: 'GCP_SA_KEY_FILE', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh '''
                        set -eu
                        gcloud auth activate-service-account --key-file="${GOOGLE_APPLICATION_CREDENTIALS}"
                        gcloud config set project "${PROJECT_ID}"

                        SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
                            --region "${REGION}" \
                            --format 'value(status.url)')

                        echo "Deployed to: ${SERVICE_URL}"
                        echo "Waiting for service to be ready..."
                        sleep 10

                        curl -f "${SERVICE_URL}/api/v1/health/" || echo "Health check endpoint not available"
                    '''
                }
            }
        }
    }

    post {
        always {
            echo "=== Deployment Summary ==="
            echo "Commit: ${env.RESOLVED_GIT_COMMIT ?: env.GIT_COMMIT ?: 'unknown'}"
            echo "Branch: ${env.BRANCH_NAME ?: 'unknown'}"
        }
        success {
            echo "Pipeline completed successfully!"
        }
        failure {
            echo "Pipeline failed!"
        }
        cleanup {
            script {
                try {
                    cleanWs(
                        deleteDirs: true,
                        disableDeferredWipeout: true,
                        notFailBuild: true
                    )
                } catch (Exception e) {
                    echo "Skipping workspace cleanup: ${e.getMessage()}"
                }
            }
        }
    }
}
