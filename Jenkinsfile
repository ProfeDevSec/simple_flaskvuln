pipeline {
  agent any

  environment {
    APP_URL       = 'http://localhost:5000'
    SONAR_HOST    = 'http://sonarqube-custom:9000/'
    REPORT_DIR    = 'zap-reports'
    DC_HOME       = tool 'dependency-check'
  }

  stages {

    stage('Build') {
      steps {
        sh 'docker build -t flask-vuln-app:${BUILD_NUMBER} .'
      }
    }

    stage('Test - Unit') {
      steps {
        sh 'pip install pytest flask && pytest tests/ --junitxml=results.xml || true'
        junit allowEmptyResults: true, testResults: 'results.xml'
      }
    }

    stage('Deploy - Staging') {
      steps {
        sh '''
          docker rm -f flask-app || true
          docker run -d --name flask-app -p 5000:5000 flask-vuln-app:${BUILD_NUMBER}
          sleep 5+
          curl -sf http://localhost:5000/hello?name=test || echo "App no responde"
        '''
      }
    }
stage('Analyze - SonarQube') {
    steps {
        withSonarQubeEnv('sonarqube-server') {
            withEnv(["PATH+SONAR=${tool 'sonarqube-scanner'}/bin"]) {
                sh """
                    sonar-scanner \
                      -Dsonar.projectKey=devsecops-lab \
                      -Dsonar.sources=. \
                      -Dsonar.python.version=3
                """
            }
        }
    }
}

stage('Security Test - SCA Dependencies') {
    steps {
        sh """
            mkdir -p \${WORKSPACE}/dc-report
            chmod 777 \${WORKSPACE}/dc-report

            docker run --rm \
              --network devsecops-network \
              -v \${WORKSPACE}:/src \
              -v \${WORKSPACE}/dc-report:/report \
              -v dc-nvd-data:/usr/share/dependency-check/data \
              --user \$(id -u):\$(id -g) \
              owasp/dependency-check:latest \
                --scan /src \
                --format HTML \
                --format XML \
                --out /report \
                --project devsecops-lab \
                --noupdate

            chmod -R 755 \${WORKSPACE}/dc-report    
        """
        dependencyCheckPublisher(
            pattern: 'dc-report/dependency-check-report.xml'
        )
    }
}    


stage('Security Test - DAST ZAP') {
    steps {
        sh """
            rm -rf \${WORKSPACE}/zap-reports
            mkdir -p \${WORKSPACE}/zap-reports
            chmod 777 \${WORKSPACE}/zap-reports

            docker run --rm \
              --network host \
              -v \${WORKSPACE}/zap-reports:/zap/wrk/:rw \
              --user \$(id -u):\$(id -g) \
              ghcr.io/zaproxy/zaproxy:stable \
                zap-baseline.py \
                  -t http://localhost:5000/hello?name=test \
                  -r zap_report.html \
                  -J zap_report.json \
                  --auto || true
        """

        publishHTML(target: [
            allowMissing         : true,
            alwaysLinkToLastBuild: true,
            keepAll              : true,
            reportDir            : 'zap-reports',
            reportFiles          : 'zap_report.html',
            reportName           : 'OWASP ZAP Report'
        ])
    }
}

  post {
    always {
      archiveArtifacts artifacts: '**/*.html,**/*.xml,**/*.json', allowEmptyArchive: true
      sh 'docker rm -f flask-app || true'
    }
  }
}
