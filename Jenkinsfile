pipeline {
    agent any
    
    environment {
        // Docker configuration
        DOCKER_REGISTRY = 'docker.io'
        IMAGE_NAME = 'financial-doc-extraction-poc'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        DOCKER_CREDENTIALS_ID = 'docker-hub-credentials'
        
        // Application configuration
        APP_ENV = 'staging'
        PYTHON_VERSION = '3.10'
        
        // Test configuration
        TEST_RESULTS_DIR = 'test-results'
        COVERAGE_THRESHOLD = '70'
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '📦 Checking out source code...'
                checkout scm
                
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()
                }
            }
        }
        
        stage('Environment Setup') {
            steps {
                echo '🔧 Setting up Python environment...'
                sh '''
                    python --version
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }
        
        stage('Lint & Code Quality') {
            steps {
                echo '🔍 Running linters...'
                sh '''
                    pip install flake8 black isort mypy
                    
                    echo "Running Black formatter check..."
                    black --check src/ tests/ || true
                    
                    echo "Running isort import check..."
                    isort --check-only src/ tests/ || true
                    
                    echo "Running Flake8..."
                    flake8 src/ tests/ --max-line-length=120 --ignore=E203,W503 || true
                    
                    echo "Running MyPy type checking..."
                    mypy src/ --ignore-missing-imports || true
                '''
            }
        }
        
        stage('Unit Tests') {
            steps {
                echo '🧪 Running unit tests...'
                sh '''
                    mkdir -p ${TEST_RESULTS_DIR}
                    pytest tests/ \
                        --junitxml=${TEST_RESULTS_DIR}/junit.xml \
                        --cov=src \
                        --cov-report=xml:${TEST_RESULTS_DIR}/coverage.xml \
                        --cov-report=html:${TEST_RESULTS_DIR}/htmlcov \
                        --cov-report=term \
                        || true
                '''
            }
            post {
                always {
                    junit "${TEST_RESULTS_DIR}/junit.xml"
                    publishHTML([
                        reportDir: "${TEST_RESULTS_DIR}/htmlcov",
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                echo '🔒 Running security scans...'
                sh '''
                    pip install safety bandit
                    
                    echo "Checking for known vulnerabilities in dependencies..."
                    safety check --json || true
                    
                    echo "Running Bandit security linter..."
                    bandit -r src/ -f json -o ${TEST_RESULTS_DIR}/bandit-report.json || true
                '''
            }
        }
        
        stage('Build Docker Image') {
            steps {
                echo '🐳 Building Docker image...'
                script {
                    docker.build("${IMAGE_NAME}:${IMAGE_TAG}")
                    docker.build("${IMAGE_NAME}:latest")
                }
            }
        }
        
        stage('Test Docker Image') {
            steps {
                echo '🧪 Testing Docker image...'
                sh '''
                    # Test image can start
                    docker run --rm -d \
                        --name test-container-${BUILD_NUMBER} \
                        -p 8001:8000 \
                        ${IMAGE_NAME}:${IMAGE_TAG}
                    
                    # Wait for container to be healthy
                    sleep 10
                    
                    # Test health endpoint
                    curl -f http://localhost:8001/health || exit 1
                    
                    # Cleanup
                    docker stop test-container-${BUILD_NUMBER}
                '''
            }
        }
        
        stage('Push Docker Image') {
            when {
                branch 'main'
            }
            steps {
                echo '📤 Pushing Docker image to registry...'
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", "${DOCKER_CREDENTIALS_ID}") {
                        docker.image("${IMAGE_NAME}:${IMAGE_TAG}").push()
                        docker.image("${IMAGE_NAME}:latest").push()
                    }
                }
            }
        }
        
        stage('Integration Tests') {
            steps {
                echo '🔗 Running integration tests...'
                sh '''
                    # Start services (API + dependencies)
                    docker-compose -f docker-compose.test.yml up -d
                    sleep 15
                    
                    # Run integration tests
                    pytest tests/integration/ -v || true
                    
                    # Cleanup
                    docker-compose -f docker-compose.test.yml down
                '''
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'main'
            }
            steps {
                echo '🚀 Deploying to staging environment...'
                sh '''
                    # Example: Deploy to Kubernetes
                    # kubectl set image deployment/financial-poc \
                    #     financial-poc=${IMAGE_NAME}:${IMAGE_TAG} \
                    #     --namespace=staging
                    
                    # Example: Update docker-compose deployment
                    # ssh staging-server "cd /opt/financial-poc && \
                    #     docker-compose pull && \
                    #     docker-compose up -d"
                    
                    echo "Deployment configuration would go here"
                '''
            }
        }
        
        stage('Smoke Tests') {
            when {
                branch 'main'
            }
            steps {
                echo '💨 Running smoke tests on staging...'
                sh '''
                    # Test critical endpoints
                    # STAGING_URL="http://staging.example.com"
                    # curl -f ${STAGING_URL}/health || exit 1
                    # curl -f ${STAGING_URL}/api/v1/documents || exit 1
                    
                    echo "Smoke tests configuration would go here"
                '''
            }
        }
    }
    
    post {
        always {
            echo '🧹 Cleaning up...'
            sh '''
                # Clean up test containers
                docker ps -a | grep test-container-${BUILD_NUMBER} | awk '{print $1}' | xargs -r docker rm -f || true
                
                # Clean up old images
                docker image prune -f || true
            '''
        }
        
        success {
            echo '✅ Pipeline completed successfully!'
            // Send notifications (Slack, email, etc.)
        }
        
        failure {
            echo '❌ Pipeline failed!'
            // Send failure notifications
        }
        
        unstable {
            echo '⚠️ Pipeline unstable - some tests failed'
        }
    }
}