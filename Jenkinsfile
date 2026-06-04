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
          sleep 5
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
            docker run --rm \
              --network devsecops-network \
              -v \${WORKSPACE}:/src \
              -v \${WORKSPACE}/dc-report:/report \
              owasp/dependency-check:latest \
                --scan /src \
                --format HTML \
                --format XML \
                --out /report \
                --project devsecops-lab
        """
        dependencyCheckPublisher(
            pattern: '**/dc-report/dependency-check-report.xml'
        )
    }
}

    stage('Security Test - DAST ZAP') {
      steps {
        sh """
          mkdir -p ${REPORT_DIR}
          docker run --rm --network host \\
            -v \$(pwd)/${REPORT_DIR}:/zap/wrk \\
            ghcr.io/zaproxy/zaproxy:stable \\
            zap-baseline.py \\
              -t ${APP_URL} \\
              -r zap_report.html \\
              -J zap_report.json --auto || true
        """
        publishHTML target: [
          allowMissing: true, alwaysLinkToLastBuild: true,
          reportDir: "${REPORT_DIR}", reportFiles: 'zap_report.html',
          reportName: 'OWASP ZAP Report'
        ]
      }
    }

  }

  post {
    always {
      archiveArtifacts artifacts: '**/*.html,**/*.xml,**/*.json', allowEmptyArchive: true
      sh 'docker rm -f flask-app || true'
    }
  }
}
