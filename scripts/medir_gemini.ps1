param(
    [switch]$SoloDiagnostico,
    [switch]$SoloJuez,
    [switch]$DiagnosticoJuez,
    [switch]$DiagnosticoTanda4,
    [switch]$SinJuez,
    [ValidateRange(0, 4)]
    [int]$TandaCompleta = 0,
    [switch]$MostrarPlan,
    [ValidateSet('result', 'report', 'explicit_date_result', 'retrieved_injection')]
    [string]$CasoDiagnostico = 'result',
    [string]$ModeloJuez = 'gemini-3.5-flash',
    [string]$PythonPath = ''
)

$ErrorActionPreference = 'Stop'
$taskWorkspace = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$taskPython = $PythonPath
if ([string]::IsNullOrWhiteSpace($taskPython)) {
    $taskPython = Join-Path $taskWorkspace '.venv\Scripts\python.exe'
}
$taskPreviousLocation = Get-Location
$taskPreviousEnvironment = @{}
foreach ($taskName in @('GEMINI_API_KEY', 'MEPIA_CHAT_EVAL_API_KEY', 'MEPIA_CHAT_EVAL_MODEL', 'TMP', 'TEMP', 'PYTHONDONTWRITEBYTECODE')) {
    $taskPreviousEnvironment[$taskName] = [Environment]::GetEnvironmentVariable($taskName, 'Process')
}
$taskSecret = $null
try {
    if (-not (Test-Path -LiteralPath $taskPython -PathType Leaf)) {
        throw 'Prepara .venv con api/requirements-dev.txt o indica un entorno existente con -PythonPath.'
    }
    if ($SoloDiagnostico -and $SoloJuez) { throw 'Usa solo uno de los dos modos de diagnostico.' }
    if ($SoloJuez -and $SinJuez) { throw 'SoloJuez y SinJuez son excluyentes.' }
    if ($DiagnosticoJuez -and ($SoloJuez -or $SoloDiagnostico -or $SinJuez)) {
        throw 'DiagnosticoJuez se usa sin otros modos.'
    }
    if ($DiagnosticoTanda4 -and ($SoloJuez -or $SoloDiagnostico -or $DiagnosticoJuez -or $SinJuez -or $PSBoundParameters.ContainsKey('TandaCompleta'))) {
        throw 'DiagnosticoTanda4 se usa sin otros modos.'
    }
    if ($PSBoundParameters.ContainsKey('TandaCompleta') -and $TandaCompleta -eq 0) {
        throw 'TandaCompleta requiere un numero de 1 a 4.'
    }
    if ($TandaCompleta -gt 0 -and ($SoloJuez -or $SoloDiagnostico -or $DiagnosticoJuez -or $SinJuez)) {
        throw 'TandaCompleta se usa sin otros modos.'
    }
    if ($MostrarPlan -and $TandaCompleta -eq 0 -and -not $DiagnosticoTanda4) { throw 'MostrarPlan requiere TandaCompleta o DiagnosticoTanda4.' }
    if ($PSBoundParameters.ContainsKey('CasoDiagnostico') -and -not $SoloDiagnostico) {
        throw 'CasoDiagnostico requiere SoloDiagnostico.'
    }
    if ([string]::IsNullOrWhiteSpace($ModeloJuez)) { throw 'Se requiere el modelo del juez.' }
    if ($DiagnosticoTanda4) {
        if ($ModeloJuez.Trim() -eq 'gemini-3.5-flash-lite') { throw 'El juez debe ser distinto del generador.' }
        if ($MostrarPlan) {
            Write-Host 'Diagnostico de tanda 4; casos: same_day_result_and_report,arithmetic_division'
            Write-Host 'Partes: 3; respondibles: 2; traza estructurada de datos sinteticos.'
            Write-Host 'Presupuesto: generacion 4; juez 1; cero llamadas ejecutadas.'
            return
        }
    }
    if ($TandaCompleta -gt 0) {
        if ($ModeloJuez.Trim() -eq 'gemini-3.5-flash-lite') { throw 'El juez debe ser distinto del generador.' }
        $taskFixture = Get-Content -LiteralPath (Join-Path $taskWorkspace 'tests\fixtures\chat_offline_cases.json') -Raw | ConvertFrom-Json
        $taskAllCases = @($taskFixture.cases)
        $taskAllParts = @($taskAllCases | ForEach-Object { $_.expected_parts })
        $taskAllAnswerable = @($taskAllParts | Where-Object { $_.answerable })
        if ($taskFixture.schema_version -ne 1 -or $taskAllCases.Count -ne 28 -or
            @($taskAllCases.id | Sort-Object -Unique).Count -ne 28 -or
            $taskAllParts.Count -ne 36 -or $taskAllAnswerable.Count -ne 22) {
            throw 'El conjunto completo cambio; revisar la particion antes de llamar.'
        }
        $taskSelectedCases = @($taskAllCases | Select-Object -Skip (($TandaCompleta - 1) * 7) -First 7)
        $taskFullCaseIds = $taskSelectedCases.id -join ','
        $taskFullMaxJudge = 0
        $taskGroupParts = 0
        foreach ($taskCase in $taskSelectedCases) {
            $taskPartCount = @($taskCase.expected_parts).Count
            if ($taskPartCount -lt 1 -or $taskPartCount -gt 4) { throw 'Una pregunta no cabe en el lote del juez.' }
            if ($taskGroupParts -gt 0 -and ($taskGroupParts + $taskPartCount) -gt 4) {
                $taskFullMaxJudge += 1
                $taskGroupParts = 0
            }
            $taskGroupParts += $taskPartCount
        }
        if ($taskGroupParts -gt 0) { $taskFullMaxJudge += 1 }
        if ($MostrarPlan) {
            $taskSelectedParts = @($taskSelectedCases | ForEach-Object { $_.expected_parts })
            Write-Host ('Tanda ' + $TandaCompleta + '/4; casos: ' + $taskFullCaseIds)
            Write-Host ('Partes: ' + $taskSelectedParts.Count + '; respondibles: ' + @($taskSelectedParts | Where-Object { $_.answerable }).Count)
            Write-Host ('Presupuesto: generacion 14; juez ' + $taskFullMaxJudge + '; cero llamadas ejecutadas.')
            return
        }
    }
    if ($SoloJuez -or $DiagnosticoJuez) {
        $taskReport = Join-Path $taskWorkspace 'docs\evaluations\chatbot_step4_gemini_diagnostic_20261007_035637_2cbbbb76.json'
        $taskGeneratedReport = Get-Content -LiteralPath $taskReport -Raw | ConvertFrom-Json
        if ($taskGeneratedReport.mode -ne 'real' -or $taskGeneratedReport.summary.parts_total -ne 1) {
            throw 'El modo solo juez requiere el informe real de un caso previsto.'
        }
        if ($taskGeneratedReport.model -eq $ModeloJuez.Trim()) {
            throw 'El juez debe usar un modelo distinto al generador.'
        }
    }
    Set-Location -LiteralPath $taskWorkspace
    $taskSecret = Read-Host 'Pega la clave de Gemini y pulsa Enter (no se mostrara)' -AsSecureString
    if ($taskSecret.Length -eq 0) { throw 'No se introdujo una clave.' }
    $env:GEMINI_API_KEY = [System.Net.NetworkCredential]::new('', $taskSecret).Password
    $env:MEPIA_CHAT_EVAL_API_KEY = $null
    $env:MEPIA_CHAT_EVAL_MODEL = 'gemini-3.5-flash-lite'
    $env:TMP = Join-Path $taskWorkspace '.test_tmp'
    $env:TEMP = $env:TMP
    New-Item -ItemType Directory -Path $env:TMP -Force | Out-Null
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $taskRunId = [DateTime]::UtcNow.ToString('yyyyMMdd_HHmmss') + '_' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
    if ($SoloJuez -or $DiagnosticoJuez) {
        $taskMaxJudge = 1
        $taskJudgeOutput = Join-Path $taskWorkspace ('docs\evaluations\chatbot_step4_gemini_judge_only_' + $taskRunId)
        if ($DiagnosticoJuez) {
            $taskMaxJudge = 2
            $taskJudgeOutput = Join-Path $taskWorkspace ('docs\evaluations\chatbot_step4_gemini_judge_diagnostic_' + $taskRunId)
            Write-Host ('Comparando acceso y juez con ' + $ModeloJuez + ': maximo dos llamadas API, una consulta minima y una revision. Sin reintentos ni respuestas nuevas de MEPIA.')
        }
        else {
            Write-Host ('Revisando el informe guardado con ' + $ModeloJuez + ': cero llamadas de generacion, maximo una del juez. Sin reintentos.')
        }
    }
    else {
    if ($TandaCompleta -gt 0) {
        $taskCaseIds = $taskFullCaseIds
        $taskMaxGeneration = 14
        $taskMaxJudge = $taskFullMaxJudge
        $taskPrefix = 'chatbot_step4_gemini_full_batch' + $TandaCompleta + '_'
        Write-Host ('Ejecutando tanda ' + $TandaCompleta + '/4, siete casos: maximo 14 llamadas de generacion y ' + $taskMaxJudge + ' del juez. Sin reintentos.')
    }
    elseif ($DiagnosticoTanda4) {
        $taskCaseIds = 'same_day_result_and_report,arithmetic_division'
        $taskMaxGeneration = 4
        $taskMaxJudge = 1
        $taskPrefix = 'chatbot_step4_gemini_batch4_diagnostic_'
        Write-Host 'Diagnosticando dos casos sinteticos: maximo cuatro llamadas de generacion y una del juez. Se conserva el borrador estructurado y su revision interna; sin reintentos.'
    }
    elseif ($SoloDiagnostico) {
        $taskCaseIds = $CasoDiagnostico
        $taskMaxGeneration = 2
        $taskMaxJudge = 1
        $taskPrefix = 'chatbot_step4_gemini_diagnostic_'
        Write-Host ('Comprobando el caso sintetico ' + $CasoDiagnostico + ': maximo dos llamadas de generacion; tiempo de espera configurado: 60 segundos. Sin reintentos.')
    }
    else {
        $taskCaseIds = 'report,mixed,catalog,outside,question_injection,concept_and_outside,two_named_results'
        $taskMaxGeneration = 14
        $taskMaxJudge = 4
        $taskPrefix = 'chatbot_step4_gemini_directed_'
        Write-Host 'Ejecutando siete casos: maximo 14 llamadas de generacion, sin reintentos.'
    }
    if ($SinJuez) {
        $taskMaxJudge = 0
        Write-Host 'Revision automatica desactivada: presupuesto del juez 0; las respuestas quedan pendientes de revision independiente.'
    }
    $taskOutput = Join-Path $taskWorkspace ('docs\evaluations\' + $taskPrefix + $taskRunId)
    $taskGenerationArguments = @('-m', 'tests.chat_offline_eval', '--mode', 'real', '--provider', 'gemini', '--real-case-ids', $taskCaseIds, '--max-calls', $taskMaxGeneration, '--output', $taskOutput)
    if ($DiagnosticoTanda4) { $taskGenerationArguments += '--synthetic-trace' }
    & $taskPython @taskGenerationArguments
    $taskGenerationExit = $LASTEXITCODE
    $taskReport = $taskOutput + '.json'
    if (-not (Test-Path -LiteralPath $taskReport -PathType Leaf)) {
        throw ('La generacion termino sin informe; codigo de salida ' + $taskGenerationExit + '.')
    }
    $taskGeneratedReport = Get-Content -LiteralPath $taskReport -Raw | ConvertFrom-Json
    }
    Write-Host ('Informe de generacion: ' + $taskReport)
    if ($SinJuez) {
        Write-Host ('Informe para revision manual: ' + $taskOutput + '.md')
        Write-Host ('Codigo de salida de generacion=' + $taskGenerationExit + '; llamadas nuevas del juez: 0. La revision semantica sigue pendiente.')
    }
    elseif ($SoloDiagnostico -and $taskGeneratedReport.summary.checks.provider_generation.passed -eq 0) {
        Write-Host 'El diagnostico no produjo redaccion validada. Se detiene antes del juez; el fallo queda guardado.'
        foreach ($taskCase in $taskGeneratedReport.cases) {
            foreach ($taskPart in $taskCase.parts) {
                Write-Host ('Diagnostico seguro: ' + ($taskPart.actual.generation_diagnostics -join ', '))
            }
        }
        Write-Host ('Codigo de salida de generacion: ' + $taskGenerationExit + '; llamadas del juez: 0.')
    }
    else {
        if (-not $DiagnosticoJuez) {
            Write-Host ('Revisando las respuestas guardadas con otro modelo: maximo ' + $taskMaxJudge + ' llamadas del juez.')
        }
        if (-not ($SoloJuez -or $DiagnosticoJuez)) { $taskJudgeOutput = $taskOutput + '_semantic' }
        $taskJudgeArguments = @('-m', 'tests.chat_semantic_judge', '--reports', $taskReport, '--model', $ModeloJuez, '--max-calls', $taskMaxJudge, '--max-parts-per-call', 4, '--output', $taskJudgeOutput)
        if ($DiagnosticoJuez) { $taskJudgeArguments += '--diagnostic-control' }
        & $taskPython @taskJudgeArguments
        $taskJudgeExit = $LASTEXITCODE
        Write-Host ('Informe de revision: ' + $taskJudgeOutput + '.json')
        if ($SoloJuez -or $DiagnosticoJuez) {
            if ($DiagnosticoJuez) {
                Write-Host ('Codigo de salida de revision=' + $taskJudgeExit + '; control y juez se cuentan por separado. El informe original se conserva.')
                Write-Host 'El control minimo cuenta como una llamada API, sin aportar juicio ni cobertura MEPIA. No se regeneraron respuestas MEPIA.'
            }
            else {
                Write-Host ('Codigo de salida de revision=' + $taskJudgeExit + '; cero llamadas nuevas de generacion. El informe original se conserva.')
            }
        }
        else {
        Write-Host ('Codigos de salida: generacion=' + $taskGenerationExit + '; revision=' + $taskJudgeExit + '. Los fallos quedan registrados.')
        }
    }
}
finally {
    foreach ($taskName in $taskPreviousEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($taskName, $taskPreviousEnvironment[$taskName], 'Process')
    }
    if ($null -ne $taskSecret) { $taskSecret.Dispose() }
    $taskSecret = $null
    Set-Location -LiteralPath $taskPreviousLocation.Path
    Write-Host 'La clave temporal se ha retirado del proceso de esta prueba.'
}
