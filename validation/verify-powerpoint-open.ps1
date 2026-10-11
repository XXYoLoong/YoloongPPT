[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string[]]$InputPptx,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [switch]$VerifyTextEdit,
    [switch]$IncludeContent
)

# External Windows/Office evidence only; this is not a product runtime adapter.
# Never equate headless COM opening (alerts may be suppressed) with AC-028.
$ErrorActionPreference = 'Stop'
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = '1'

function Assert-NonSystemPath([string]$Path) {
    $full = [System.IO.Path]::GetFullPath($Path)
    if ([System.IO.Path]::GetPathRoot($full) -eq 'C:\') {
        throw "Project inputs, evidence and temporary files must not use C: ($full)"
    }
    return $full
}

function Release-Com($Object) {
    if ($null -ne $Object -and [System.Runtime.InteropServices.Marshal]::IsComObject($Object)) {
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($Object)
    }
}

function Get-TextHash([string]$Text) {
    return [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData(
        [System.Text.Encoding]::UTF8.GetBytes($Text))).ToLowerInvariant()
}

function Get-ShapeSnapshot($Shape) {
    $typeNames = @{1='AutoShape';3='Chart';6='Group';9='Line';11='LinkedPicture';13='Picture';14='Placeholder';17='TextBox';19='Table'}
    $type = [int]$Shape.Type
    $item = [ordered]@{
        shape_id = [int]$Shape.Id; name = [string]$Shape.Name
        type = $type; type_name = $(if ($typeNames.ContainsKey($type)) {$typeNames[$type]} else {'Other'})
        left_pt = [double]$Shape.Left; top_pt = [double]$Shape.Top
        width_pt = [double]$Shape.Width; height_pt = [double]$Shape.Height
        rotation_degrees = [double]$Shape.Rotation; z_order = [int]$Shape.ZOrderPosition
        has_text_frame = ([int]$Shape.HasTextFrame -eq -1)
        has_table = ([int]$Shape.HasTable -eq -1); has_chart = ([int]$Shape.HasChart -eq -1)
        text = $null; table = $null; chart = $null; children = @()
    }
    $frame = $range = $table = $rows = $columns = $chart = $series = $group = $null
    try {
        if ($item.has_text_frame) {
            $frame = $Shape.TextFrame
            $range = $frame.TextRange
            $text = [string]$range.Text
            $item.text = [ordered]@{sha256=(Get-TextHash $text); characters=$text.Length}
            if ($IncludeContent) {$item.text.content=$text}
        }
        if ($item.has_table) {
            $table = $Shape.Table; $rows = $table.Rows; $columns = $table.Columns
            $cells = [System.Collections.Generic.List[string]]::new()
            for ($r=1; $r -le $rows.Count; $r++) {
                for ($c=1; $c -le $columns.Count; $c++) {
                    $cell = $cellShape = $cellFrame = $cellRange = $null
                    try {
                        $cell = $table.Cell($r,$c); $cellShape = $cell.Shape
                        $cellFrame = $cellShape.TextFrame; $cellRange = $cellFrame.TextRange
                        $cells.Add([string]$cellRange.Text)
                    } finally {
                        Release-Com $cellRange; Release-Com $cellFrame; Release-Com $cellShape; Release-Com $cell
                    }
                }
            }
            $item.table = [ordered]@{rows=[int]$rows.Count; columns=[int]$columns.Count; cell_text_sha256=(Get-TextHash ($cells.ToArray() | ConvertTo-Json -Compress))}
        }
        if ($item.has_chart) {
            $chart = $Shape.Chart; $series = $chart.SeriesCollection()
            $item.chart = [ordered]@{chart_type=[int]$chart.ChartType; series_count=[int]$series.Count; embedded_workbook_edit_tested=$false}
            if ($IncludeContent) {
                $data=[System.Collections.Generic.List[object]]::new()
                for ($i=1; $i -le $series.Count; $i++) {
                    $seriesItem=$null
                    try {
                        $seriesItem=$series.Item($i)
                        $data.Add([ordered]@{index=$i; name=[string]$seriesItem.Name; values=@($seriesItem.Values); categories=@($seriesItem.XValues)})
                    } finally {Release-Com $seriesItem}
                }
                $item.chart.series=$data.ToArray()
            }
        }
        if ($type -eq 6) {
            $group = $Shape.GroupItems
            $children = [System.Collections.Generic.List[object]]::new()
            for ($i=1; $i -le $group.Count; $i++) {
                $child = $null
                try {$child=$group.Item($i); $children.Add((Get-ShapeSnapshot $child))}
                finally {Release-Com $child}
            }
            $item.children = $children.ToArray()
        }
    } finally {
        Release-Com $group; Release-Com $series; Release-Com $chart
        Release-Com $columns; Release-Com $rows; Release-Com $table
        Release-Com $range; Release-Com $frame
    }
    return $item
}

function Get-PresentationSnapshot($Presentation) {
    $slides = $setup = $null
    try {
        $slides = $Presentation.Slides; $setup = $Presentation.PageSetup
        $pages = [System.Collections.Generic.List[object]]::new()
        for ($i=1; $i -le $slides.Count; $i++) {
            $slide = $shapes = $null
            try {
                $slide = $slides.Item($i); $shapes = $slide.Shapes
                $objects = [System.Collections.Generic.List[object]]::new()
                for ($j=1; $j -le $shapes.Count; $j++) {
                    $shape = $null
                    try {$shape=$shapes.Item($j); $objects.Add((Get-ShapeSnapshot $shape))}
                    finally {Release-Com $shape}
                }
                $pages.Add([ordered]@{index=$i; slide_id=[int]$slide.SlideId; name=[string]$slide.Name; shapes=$objects.ToArray()})
            } finally {Release-Com $shapes; Release-Com $slide}
        }
        return [ordered]@{
            slide_count=[int]$slides.Count; width_pt=[double]$setup.SlideWidth
            height_pt=[double]$setup.SlideHeight; slides=$pages.ToArray()
        }
    } finally {Release-Com $setup; Release-Com $slides}
}

function Get-PackageHashes([string]$Path) {
    $zip = [System.IO.Compression.ZipFile]::OpenRead($Path)
    $result = @{}
    try {
        foreach ($entry in $zip.Entries) {
            $stream = $entry.Open()
            try {$result[$entry.FullName] = [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($stream)).ToLowerInvariant()}
            finally {$stream.Dispose()}
        }
    } finally {$zip.Dispose()}
    return $result
}

function Verify-CopyTextEdit($Presentations, [string]$Source, [string]$Directory, $Before) {
    $copy = Join-Path $Directory 'editability-before.pptx'
    $saved = Join-Path $Directory 'editability-after.pptx'
    Copy-Item -LiteralPath $Source -Destination $copy
    $pres = $slides = $slide = $shapes = $shape = $frame = $range = $null
    $target = $null; $after = $null
    $result = [ordered]@{attempted=$true; passed=$false; copy_input=$copy; copy_output=$saved; target=$null}
    try {
        $pres = $Presentations.Open($copy,0,0,0); $slides = $pres.Slides
        foreach ($page in $Before.slides) {
            foreach ($candidate in $page.shapes) {
                if ($candidate.has_text_frame -and $candidate.text.characters -gt 0) {
                    $target = [ordered]@{slide_index=$page.index; shape_id=$candidate.shape_id; name=$candidate.name}
                    break
                }
            }
            if ($null -ne $target) {break}
        }
        if ($null -eq $target) {throw 'No nonempty top-level native text frame is available for the copy probe.'}
        $slide = $slides.Item($target.slide_index); $shapes = $slide.Shapes
        $shape = $shapes.Item($target.name); $frame = $shape.TextFrame; $range = $frame.TextRange
        $newText = [string]$range.Text + ' [COM editability probe]'
        $range.Text = $newText
        $pres.SaveAs($saved,24,0)
        $result.target = $target
        $result.expected_text_sha256 = Get-TextHash $newText
    } finally {
        Release-Com $range; Release-Com $frame; Release-Com $shape; Release-Com $shapes
        Release-Com $slide; Release-Com $slides
        if ($null -ne $pres) {try {$pres.Saved=-1; $pres.Close()} finally {Release-Com $pres; $pres=$null}}
    }
    try {
        $pres=$Presentations.Open($saved,-1,0,0)
        $after=Get-PresentationSnapshot $pres
    } finally {
        if ($null -ne $pres) {try {$pres.Close()} finally {Release-Com $pres; $pres=$null}}
    }
    $differences = [System.Collections.Generic.List[object]]::new()
    foreach ($page in $Before.slides) {
        $afterPage = @($after.slides | Where-Object slide_id -eq $page.slide_id)
        if ($afterPage.Count -ne 1) {$differences.Add([ordered]@{slide_id=$page.slide_id; reason='slide_missing_or_duplicated'}); continue}
        if ($page.name -ne $afterPage[0].name -or $page.shapes.Count -ne $afterPage[0].shapes.Count) {
            $differences.Add([ordered]@{slide_id=$page.slide_id; reason='slide_name_or_shape_count_changed'})
        }
        foreach ($obj in $page.shapes) {
            if ($page.index -eq $target.slide_index -and $obj.shape_id -eq $target.shape_id) {continue}
            $afterObj = @($afterPage[0].shapes | Where-Object shape_id -eq $obj.shape_id)
            if ($afterObj.Count -ne 1 -or ($obj | ConvertTo-Json -Depth 30 -Compress) -ne ($afterObj[0] | ConvertTo-Json -Depth 30 -Compress)) {
                $differences.Add([ordered]@{slide_id=$page.slide_id; shape_id=$obj.shape_id; reason='measured_COM_properties_changed'})
            }
        }
    }
    $edited = @($after.slides[$target.slide_index-1].shapes | Where-Object shape_id -eq $target.shape_id)
    $result.reopened = $true; $result.snapshot_after = $after
    $result.actual_text_sha256 = $edited[0].text.sha256
    $result.target_text_persisted = ($result.actual_text_sha256 -eq $result.expected_text_sha256)
    $result.non_target_measured_property_differences = $differences.ToArray()
    $result.non_target_measured_properties_preserved = ($differences.Count -eq 0)
    $result.page_dimensions_and_count_preserved = ($Before.slide_count -eq $after.slide_count -and $Before.width_pt -eq $after.width_pt -and $Before.height_pt -eq $after.height_pt)
    $beforeParts=Get-PackageHashes $Source; $afterParts=Get-PackageHashes $saved
    $result.package_part_diff = [ordered]@{
        added=@($afterParts.Keys | Where-Object {-not $beforeParts.ContainsKey($_)} | Sort-Object)
        removed=@($beforeParts.Keys | Where-Object {-not $afterParts.ContainsKey($_)} | Sort-Object)
        changed=@($beforeParts.Keys | Where-Object {$afterParts.ContainsKey($_) -and $beforeParts[$_] -ne $afterParts[$_]} | Sort-Object)
        unchanged=@($beforeParts.Keys | Where-Object {$afterParts.ContainsKey($_) -and $beforeParts[$_] -eq $afterParts[$_]} | Sort-Object)
    }
    $result.output_sha256=(Get-FileHash -LiteralPath $saved -Algorithm SHA256).Hash.ToLowerInvariant()
    $result.passed=($result.target_text_persisted -and $result.non_target_measured_properties_preserved -and $result.page_dimensions_and_count_preserved)
    $result.boundary='One native text edit on a disposable copy. Preservation compares measured COM properties only; package rewrites are recorded separately. Font runs, masters/themes, unknown parts, chart data editing, full rendering and all object properties are not certified.'
    return $result
}

$output = Assert-NonSystemPath $OutputDirectory
if (Test-Path -LiteralPath $output) {throw "Use a new output directory to preserve previous evidence: $output"}
New-Item -ItemType Directory -Path $output | Out-Null
$previousTemp=$env:TEMP; $previousTmp=$env:TMP
$env:TEMP = $env:TMP = Join-Path $output 'tmp'
New-Item -ItemType Directory -Path $env:TEMP | Out-Null
$sources = @($InputPptx | ForEach-Object {Assert-NonSystemPath $_})
foreach ($source in $sources) {
    if (-not (Test-Path -LiteralPath $source -PathType Leaf) -or [System.IO.Path]::GetExtension($source) -ne '.pptx') {throw "Invalid PPTX input: $source"}
}
$report = [ordered]@{
    schema_version=1; requirement_ids=@('AC-028','ADP-PP-01-01','TST-018','PPT-001','PPT-002','PPT-008','PPT-011','PPT-012','PPT-014','PPT-016','PPT-017')
    task_ids=@('TASK-ADP-PP-01-01','VERIFY-ADP-PP-01-01','TASK-TST-018')
    started_utc=[DateTime]::UtcNow.ToString('o'); temp_path=$env:TEMP; include_content=[bool]$IncludeContent
    status='not_run'; application=$null; inputs=@(); errors=@(); cleanup_errors=@()
    ac028_repair_prompt_observed=$false; ac028_no_repair_prompt_verified=$null; ac028_passed=$false
    boundary='Headless external COM evidence. UI repair prompts are not observed, so AC-028 remains partial. PP-01 full capability matrix and TST-018 full preservation scope are not accepted by this probe.'
    official_api_references=@('https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentations.open','https://learn.microsoft.com/en-us/office/vba/api/powerpoint.presentation.saveas','https://learn.microsoft.com/en-us/office/vba/api/powerpoint.application.displayalerts')
}
$app = $presentations = $pres = $null
$preexistingProcesses = @(Get-Process POWERPNT -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
$initialPresentationCount = $null
try {
    $app = New-Object -ComObject PowerPoint.Application
    $presentations=$app.Presentations; $initialPresentationCount=[int]$presentations.Count
    $officeConfig=Get-ItemProperty -Path 'Registry::HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Office\ClickToRun\Configuration' -ErrorAction SilentlyContinue
    $appPath=Get-ItemProperty -Path 'Registry::HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\POWERPNT.EXE' -ErrorAction SilentlyContinue
    $report.application=[ordered]@{
        name=[string]$app.Name; version=[string]$app.Version; registered_binary=$appPath.'(default)'
        binary_version=$(if (Test-Path -LiteralPath $appPath.'(default)') {(Get-Item -LiteralPath $appPath.'(default)').VersionInfo.FileVersion} else {$null})
        click_to_run_version=$officeConfig.ClientVersionToReport; display_alerts=[int]$app.DisplayAlerts
        display_alerts_changed=$false; preexisting_process_ids=$preexistingProcesses; initial_presentation_count=$initialPresentationCount
    }
    $inputs=[System.Collections.Generic.List[object]]::new()
    for ($n=0; $n -lt $sources.Count; $n++) {
        $source=$sources[$n]
        $sourceResult=Join-Path ([System.IO.Path]::GetDirectoryName($source)) 'result.json'
        $sourceRunId=$null
        if (Test-Path -LiteralPath $sourceResult -PathType Leaf) {$sourceRunId=(Get-Content -LiteralPath $sourceResult -Raw -Encoding utf8 | ConvertFrom-Json).run_id}
        $record=[ordered]@{path=$source; source_run_id=$sourceRunId; sha256_before=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant(); read_only_requested=$true; with_window=$false; opened=$false; snapshot=$null; text_edit_copy=@{attempted=$false}}
        $inputs.Add($record)
        try {
            $pres=$presentations.Open($source,-1,0,0)
            $record.opened=$true; $record.read_only_actual=([int]$pres.ReadOnly -eq -1)
            $record.snapshot=Get-PresentationSnapshot $pres
        } finally {
            if ($null -ne $pres) {try {$pres.Close()} finally {Release-Com $pres; $pres=$null}}
        }
        if ($VerifyTextEdit) {
            $copyDir=Join-Path $output ('input-{0}' -f ($n+1))
            New-Item -ItemType Directory -Path $copyDir | Out-Null
            $record.text_edit_copy=Verify-CopyTextEdit $presentations $source $copyDir $record.snapshot
        }
        $record.sha256_after=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
        $record.source_byte_preserved=($record.sha256_before -eq $record.sha256_after)
        $record.passed=($record.opened -and $record.read_only_actual -and $record.source_byte_preserved -and (-not $VerifyTextEdit -or $record.text_edit_copy.passed))
    }
    $report.inputs=$inputs.ToArray()
    $report.status=$(if (@($report.inputs | Where-Object {-not $_.passed}).Count -eq 0) {'passed_bounded_probe'} else {'failed'})
} catch {
    $report.status='failed'
    $report.errors=@([ordered]@{type=$_.Exception.GetType().FullName; message=$_.Exception.Message; hresult=$_.Exception.HResult; location=$_.InvocationInfo.PositionMessage})
    if ($null -ne $inputs) {$report.inputs=$inputs.ToArray()}
} finally {
    if ($null -ne $pres) {
        try {$pres.Saved=-1; $pres.Close()} catch {$report.cleanup_errors+= $_.Exception.Message}
        finally {Release-Com $pres}
    }
    if ($null -ne $app) {
        # Do not quit a user's PowerPoint session, including presentations
        # opened while the probe was running.
        if ($preexistingProcesses.Count -eq 0 -and $initialPresentationCount -eq 0) {
            try {if ($null -ne $presentations -and [int]$presentations.Count -eq 0) {$app.Quit()}}
            catch {$report.cleanup_errors+= $_.Exception.Message}
        }
    }
    Release-Com $presentations; Release-Com $app
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
    foreach ($record in $report.inputs) {
        $record.sha256_after=(Get-FileHash -LiteralPath $record.path -Algorithm SHA256).Hash.ToLowerInvariant()
        $record.source_byte_preserved=($record.sha256_before -eq $record.sha256_after)
    }
    $report.completed_utc=[DateTime]::UtcNow.ToString('o')
    $report.script_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $env:TEMP=$previousTemp; $env:TMP=$previousTmp
    # Office may produce diagnostic logs in TEMP. Keep only deliberate evidence.
    $temporaryRoot=[System.IO.Path]::GetFullPath((Join-Path $output 'tmp'))
    if ($temporaryRoot.StartsWith($output.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)) {
        try {Remove-Item -LiteralPath $temporaryRoot -Recurse -Force}
        catch {$report.cleanup_errors+= $_.Exception.Message}
    }
    $reportPath=Join-Path $output 'report.json'
    [System.IO.File]::WriteAllText($reportPath,($report | ConvertTo-Json -Depth 40),[System.Text.UTF8Encoding]::new($false))
    Write-Output "$($report.status): $reportPath"
}
if ($report.status -ne 'passed_bounded_probe' -or $report.cleanup_errors.Count -ne 0) {exit 1}
