pipeline {
    agent any

    environment {
        // Docker image details
        IMAGE_NAME = "taxi-analytics-api"
        
        // Ubuntu host details
        UBUNTU_HOST = "ubuntu@192.168.6.51"
        DEPLOYMENT_DIR = "/opt/taxi-analytics"
        
        // Jenkins credentials (configure in Jenkins UI: Manage Jenkins > Manage Credentials)
        // Store your API keys securely in Jenkins credentials store
        ANTHROPIC_CREDENTIAL = credentials('anthropic-api-key')
        SSH_KEY_ID = 'ubuntu-ssh-key'  // Configure SSH key credentials in Jenkins
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }

    stages {
        stage('📋 Checkout') {
            steps {
                checkout scm
                script {
                    GIT_COMMIT_SHORT = sh(returnStdout: true, script: "git rev-parse --short HEAD").trim()
                    GIT_BRANCH = sh(returnStdout: true, script: "git rev-parse --abbrev-ref HEAD").trim()
                    echo "✅ Checkout complete: ${GIT_BRANCH} @ ${GIT_COMMIT_SHORT}"
                }
            }
        }

        stage('🏗️ Build Docker Image') {
            steps {
                script {
                    echo "🔨 Building Docker image: ${IMAGE_NAME}:${BUILD_NUMBER}"
                    sh '''
                        docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} .
                        docker tag ${IMAGE_NAME}:${BUILD_NUMBER} ${IMAGE_NAME}:latest
                        docker image ls | grep ${IMAGE_NAME}
                    '''
                }
            }
        }

        stage('🧪 Container Validation') {
            steps {
                script {
                    echo "✔️ Validating container..."
                    sh '''
                        # Run container and check health
                        docker run --rm --entrypoint python ${IMAGE_NAME}:${BUILD_NUMBER} -m py_compile api_server.py
                        echo "✅ Python syntax check passed"
                        
                        # Run the automated API tests
                        echo "🧪 Running Pytest automated test suite..."
                        docker run --rm -v ${PWD}/test_api.py:/app/test_api.py --entrypoint pytest ${IMAGE_NAME}:${BUILD_NUMBER} test_api.py -v
                        echo "✅ Automated tests passed successfully"
                    '''
                }
            }
        }

        stage('🚀 Deploy to Ubuntu') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "📦 Deploying to Ubuntu server (192.168.6.51:8100)..."
                    withCredentials([sshUserPrivateKey(credentialsId: 'ubuntu-ssh-key', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
                        sh '''
                            # Copy docker-compose and Dockerfile to Ubuntu
                            scp -i ${SSH_KEY} -o StrictHostKeyChecking=no \
                                docker-compose.yml \
                                Dockerfile \
                                requirements.txt \
                                api_server.py \
                                orchestrator.py \
                                schema_specialist.py \
                                code_generator.py \
                                sandbox.py \
                                providers.py \
                                usage_tracker.py \
                                monitor.py \
                                ${SSH_USER}@192.168.6.51:${DEPLOYMENT_DIR}/
                        '''
                    }
                }
            }
        }

        stage('🐳 Start Services') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "⚡ Starting Docker containers..."
                    withCredentials([
                        string(credentialsId: 'anthropic-api-key', variable: 'ANTHROPIC_KEY')
                    ]) {
                        withCredentials([sshUserPrivateKey(credentialsId: 'ubuntu-ssh-key', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
                            sh '''
                                ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ${SSH_USER}@192.168.6.51 << 'EOF'
                                    cd ${DEPLOYMENT_DIR}
                                    
                                    echo "🛑 Stopping existing containers..."
                                    docker-compose down || true
                                    
                                    echo "🔄 Pulling latest code..."
                                    git pull origin main || true
                                    
                                    echo "🌍 Setting environment variables..."
                                    export ANTHROPIC_API_KEY="${ANTHROPIC_KEY}"
                                    
                                    echo "🚀 Starting new containers..."
                                    docker-compose up -d --build
                                    
                                    echo "⏳ Waiting for services to be ready..."
                                    sleep 5
                                    
                                    echo "✅ Containers running:"
                                    docker-compose ps
EOF
                            '''
                        }
                    }
                }
            }
        }

        stage('🏥 Health Checks') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "🔍 Running health checks..."
                    sh '''
                        # Wait for service to be ready
                        for i in {1..10}; do
                            echo "Attempt $i/10: Checking API health..."
                            if curl -f http://192.168.6.51:8100/health > /dev/null 2>&1; then
                                echo "✅ API is healthy!"
                                
                                # Get dashboard data
                                echo "📊 Dashboard metrics:"
                                curl -s http://192.168.6.51:8100/api/dashboard | python -m json.tool | head -30
                                
                                echo ""
                                echo "💰 Cost tracking:"
                                curl -s http://192.168.6.51:8100/api/costs | python -m json.tool
                                
                                exit 0
                            fi
                            sleep 3
                        done
                        
                        echo "❌ API failed to become healthy"
                        exit 1
                    '''
                }
            }
        }

        stage('📝 Log Container Status') {
            when {
                branch 'main'
            }
            steps {
                script {
                    withCredentials([sshUserPrivateKey(credentialsId: 'ubuntu-ssh-key', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
                        sh '''
                            ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ${SSH_USER}@192.168.6.51 << 'EOF'
                                echo "📋 Container logs (last 20 lines):"
                                docker-compose -f /opt/taxi-analytics/docker-compose.yml logs --tail=20
                                
                                echo ""
                                echo "📦 Running containers:"
                                docker ps --filter "name=taxi-analytics" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
EOF
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                echo "🧹 Cleaning up workspace..."
                cleanWs()
            }
        }

        success {
            echo """
            ✅ ============================================
            ✅ DEPLOYMENT SUCCESSFUL
            ✅ ============================================
            ✅ API Server: http://192.168.6.51:8100
            ✅ Health Check: http://192.168.6.51:8100/health
            ✅ Dashboard: http://192.168.6.51:8100/api/dashboard
            ✅ Costs: http://192.168.6.51:8100/api/costs
            ✅ ============================================
            """
        }

        failure {
            echo """
            ❌ ============================================
            ❌ DEPLOYMENT FAILED
            ❌ ============================================
            ❌ Check logs above for details
            ❌ Jenkins: http://192.168.6.51:8090
            ❌ ============================================
            """
        }
    }
}
