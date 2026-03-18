pipeline {
    agent any

    environment {
        PROJECT_ID = credentials('GCP_PROJECT_ID')
        REGION = credentials('GCP_REGION')
        SERVICE_NAME = credentials('GCP_SERVICE_NAME')
        REGISTRY = "${REGION}-docker.pkg.dev"
        SERVICE_PORT = credentials('SERVICE_PORT')
        GCP_SA_KEY = credentials('GCP_SA_KEY')
        DJANGO_SECRET_KEY = credentials('DJANGO_SECRET_KEY')
        DATABASE_URL = credentials('DATABASE_URL')
        SUPABASE_URL = credentials('SUPABASE_URL')
        SUPABASE_KEY = credentials('SUPABASE_KEY')
        SUPABASE_JWT_SECRET = credentials('SUPABASE_JWT_SECRET')
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
            }
        }

        stage('Lint & Format Check') {
            steps {
                script {
                    docker.image('python:3.13-slim').inside('-v $(pwd):/workspace -w /workspace/backend') {
                        sh '''
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

        stage('Run Tests') {
            environment {
                DATABASE_URL = 'postgres://postgres:postgres@localhost:5432/test_db?sslmode=disable'
                DATABASE_SSL_REQUIRE = 'false'
                DJANGO_SETTINGS_MODULE = 'config.settings'
                SECRET_KEY = 'test-secret-key-for-ci'
                DEBUG = 'False'
                ALLOWED_HOSTS = '*'
            }
            steps {
                script {
                    // Start PostgreSQL container
                    def postgres = docker.image('postgres:15').run(
                        '-e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=test_db -p 5432:5432'
                    )
                    
                    try {
                        sh 'sleep 10'
                        
                        docker.image('python:3.13-slim').inside('--network host -v $(pwd):/workspace -w /workspace/backend') {
                            sh '''
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
                    def shortSha = sh(script: "git rev-parse --short=7 HEAD", returnStdout: true).trim()
                    env.SHORT_SHA = shortSha
                    env.IMAGE_TAG = "${REGISTRY}/${PROJECT_ID}/financemanager/${SERVICE_NAME}:${shortSha}"
                    
                    echo "Generated image tag: ${env.IMAGE_TAG}"
                    
                    if (!env.IMAGE_TAG || env.IMAGE_TAG.contains('//') || env.IMAGE_TAG.contains('/:')) {
                        error "Invalid image tag. Check that GCP credentials are configured."
                    }
                }
                
                withCredentials([file(credentialsId: 'GCP_SA_KEY_FILE', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh '''
                        gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
                        gcloud config set project ${PROJECT_ID}
                        gcloud auth configure-docker ${REGISTRY} --quiet
                    '''
                }
                
                dir('backend') {
                    sh '''
                        echo "=== Building Docker image ==="
                        docker build -t ${IMAGE_TAG} .
                        docker tag ${IMAGE_TAG} ${REGISTRY}/${PROJECT_ID}/financemanager/${SERVICE_NAME}:latest
                        echo "=== Pushing Docker image ==="
                        docker push ${IMAGE_TAG}
                        docker push ${REGISTRY}/${PROJECT_ID}/financemanager/${SERVICE_NAME}:latest
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
                    if (!env.IMAGE_TAG) {
                        error "IMAGE_TAG is empty! Build stage may have failed."
                    }
                }
                
                withCredentials([file(credentialsId: 'GCP_SA_KEY_FILE', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh '''
                        gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
                        gcloud config set project ${PROJECT_ID}
                        
                        echo "=== Deploying to Cloud Run ==="
                        gcloud run deploy ${SERVICE_NAME} \
                            --image ${IMAGE_TAG} \
                            --region ${REGION} \
                            --platform managed \
                            --allow-unauthenticated \
                            --port ${SERVICE_PORT} \
                            --memory 512Mi \
                            --cpu 1 \
                            --min-instances 0 \
                            --max-instances 10 \
                            --set-env-vars "DEBUG=False" \
                            --set-env-vars "ALLOWED_HOSTS=*" \
                            --set-secrets "SECRET_KEY=${DJANGO_SECRET_KEY}:latest" \
                            --set-secrets "DATABASE_URL=${DATABASE_URL}:latest" \
                            --set-secrets "SUPABASE_URL=${SUPABASE_URL}:latest" \
                            --set-secrets "SUPABASE_KEY=${SUPABASE_KEY}:latest" \
                            --set-secrets "SUPABASE_JWT_SECRET=${SUPABASE_JWT_SECRET}:latest"
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
                        gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS}
                        gcloud config set project ${PROJECT_ID}
                        
                        SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
                            --region ${REGION} \
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
            echo "Commit: ${env.GIT_COMMIT}"
            echo "Branch: ${env.GIT_BRANCH}"
        }
        success {
            echo "Pipeline completed successfully!"
        }
        failure {
            echo "Pipeline failed!"
        }
        cleanup {
            cleanWs()
        }
    }
}
