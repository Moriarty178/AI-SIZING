pipeline {
    agent {
        label 'cnht_sizing'
    }

    environment {
        APP_REPO_URL   = 'http://10.255.60.7/cnht/sizing.git'
        CREDENTIALS_ID = 'gitlab-sizing-token'
        BRANCH_NAME    = 'staging'
    }

    stages {
        stage('1. Setup & Checkout Repo') {
            steps {
                deleteDir()
                echo "=== KÉO TOÀN BỘ CODE VỀ AGENT ==="
                git branch: "${BRANCH_NAME}",
                    credentialsId: "${CREDENTIALS_ID}",
                    url: "${APP_REPO_URL}"
                
                echo "=== COPY ENV FILES ==="
                sh '''
                    cp /home/sizing/configs/sizing.env .env
                    cp /home/sizing/configs/sizing.env backend1/.env
                '''
            }
        }

        stage('2. Build Backend (Maven)') {
            when { changeset "backend1/**" }
            steps {
                dir('backend1') {
                    sh """
                        echo "=== BẮT ĐẦU BUILD JAVA SPRING BOOT ==="
                        docker run \
                            --network=host \
                            --user \$(id -u):\$(id -g) \
                            -v /home/sizing/settings.xml:/tmp/settings.xml \
                            -v /home/sizing/.m2:/home/sizing/.m2 \
                            -e MAVEN_USER_HOME=/home/sizing \
                            -v \$(pwd):/app \
                            -w /app \
                            registry.kcntt.net/library/maven:3.9-eclipse-temurin-21-alpine \
                            mvn -s /tmp/settings.xml -Dmaven.repo.local=/home/sizing/.m2/repository clean install -DskipTests=true -U
                        ls -l target/
                    """
                }
            }
        }

        stage('3. Deploy Backend') {
            when { changeset "backend1/**" }
            steps {
                sh """
                    echo "=== KIỂM TRA FILE JAR ==="
                    ls -la backend1/target/*.jar | grep -v original \
                        || { echo '❌ Không tìm thấy file JAR!'; exit 1; }

                    echo "=== RE-DEPLOY CONTAINER BACKEND ==="
                    docker compose up -d --build --no-deps backend

                    echo "=== VERIFY BACKEND HEALTHY ==="
                    sleep 10
                    docker inspect sizing-backend \
                        --format='Status: {{.State.Status}} | Health: {{.State.Health.Status}}'
                """
            }
        }

        stage('4. Deploy Frontend (Nginx)') {
            when {
                anyOf {
                    changeset "frontend/**"
                    changeset "dashboard/**"
                    changeset "nginx/**"
                }
            }
            steps {
                sh """
                    echo "=== RE-DEPLOY CONTAINER NGINX (FRONTEND) ==="
                    docker compose up -d --build --no-deps nginx

                    echo "=== VERIFY NGINX RUNNING ==="
                    docker ps | grep nginx \
                        || { echo '❌ Nginx không chạy được!'; exit 1; }
                """
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline thành công!'
        }
        failure {
            echo '❌ Pipeline thất bại!!!'
        }
        always {
            node('cnht_sizing') {
                sh 'docker image prune -f || true'
            }
        }
    }
}