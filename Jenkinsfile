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
      # Crear volumen limpio para los reportes
      docker volume rm dc-report-vol 2>/dev/null || true
      docker volume create dc-report-vol

      # Correr dependency-check escribiendo en el volumen (sin problemas de permisos)
      docker run --rm \
        --network devsecops-network \
        -v \${WORKSPACE}:/src:ro \
        -v dc-report-vol:/report \
        -v dc-nvd-data:/usr/share/dependency-check/data \
        owasp/dependency-check:latest \
          --scan /src \
          --format HTML \
          --format XML \
          --out /report \
          --project devsecops-lab \
          --noupdate || true

      # Verificar que el volumen tiene contenido
      docker run --rm \
        -v dc-report-vol:/report \
        alpine ls -la /report/

      docker run --rm \
        -v dc-report-vol:/report \
        alpine cat /report/dependency-check-report.xml  

      # Copiar del volumen al workspace con permisos correctos
      mkdir -p \${WORKSPACE}/dc-report
    """
    sh '''  
      docker run --rm \
        -v dc-report-vol:/report \
        -v \${WORKSPACE}/dc-report:/dest \
        alpine sh -c 'cp /report/*.html /dest/ && cp /report/*.xml /dest/ && chmod 644 /dest/*'

      echo "=== Archivos copiados al workspace ==="
      ls -la \${WORKSPACE}/dc-report/
    '''

    publishHTML(target: [
      allowMissing         : true,
      alwaysLinkToLastBuild: true,
      keepAll              : true,
      reportDir            : "${WORKSPACE}/dc-report",
      reportFiles          : 'dependency-check-report.html',
      reportName           : 'Dependency-Check Report'
    ])
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
          ghcr.io/zaproxy/zaproxy:stable \
            zap-baseline.py \
              -t http://localhost:5000/hello?name=test \
              -r zap_report.html \
              -J zap_report.json \
              --auto || true
  
        echo "=== Contenido zap-reports ==="
        ls -la \${WORKSPACE}/zap-reports/
      """
  
      publishHTML(target: [
        allowMissing         : true,
        alwaysLinkToLastBuild: true,
        keepAll              : true,
        reportDir            : "${WORKSPACE}/zap-reports",
        reportFiles          : 'zap_report.html',
        reportName           : 'OWASP ZAP Report'
      ])
      sh 'find ${WORKSPACE} -name "*.html" -o -name "*.xml" -o -name "*.json" 2>/dev/null | head -30'
    }
}
}

  post {
    always {
      sh """
        cp \${WORKSPACE}/dc-report/*.html \${WORKSPACE}/ 2>/dev/null || true
        cp \${WORKSPACE}/dc-report/*.xml \${WORKSPACE}/ 2>/dev/null || true
        cp \${WORKSPACE}/zap-reports/*.html \${WORKSPACE}/ 2>/dev/null || true
        cp \${WORKSPACE}/zap-reports/*.json \${WORKSPACE}/ 2>/dev/null || true
      """

      archiveArtifacts(
        artifacts         : 'dependency-check-report.html,dependency-check-report.xml,zap_report.html,zap_report.json',
        allowEmptyArchive : true
      )
      sh 'docker rm -f flask-app || true'
    }
  }
}
