using System.IO.Compression;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Xml.Linq;
using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Validation;
using A = DocumentFormat.OpenXml.Drawing;
using P = DocumentFormat.OpenXml.Presentation;

const string RouteId = "PP-04";
const string TaskId = "ADP-PP-04-01";
const string SourceRevision = "278b47b1dedd5b46ee84c286e77cdfb0bf4594be";
const string SourceSampleSha256 = "e10cc9e120961f6bd4074a373c9c80d2a06c497157e8f4972977b7bea83a8f34";

var root = AppContext.BaseDirectory;
var projectRoot = Directory.GetCurrentDirectory();
var fixturePath = Path.Combine(projectRoot, "fixtures", "python-pptx-default.pptx");
var artifacts = Path.Combine(projectRoot, "artifacts");
Directory.CreateDirectory(artifacts);

if (!File.Exists(fixturePath))
{
    throw new FileNotFoundException("The pinned real PPTX fixture is missing.", fixturePath);
}

var fixtureHash = Sha256File(fixturePath);
if (!fixtureHash.Equals(SourceSampleSha256, StringComparison.OrdinalIgnoreCase))
{
    throw new InvalidDataException($"Fixture SHA-256 mismatch: {fixtureHash}");
}

var inputInventory = InspectPresentation(fixturePath);
var outputPath = Path.Combine(artifacts, "pp04-output.pptx");
File.Copy(fixturePath, outputPath, overwrite: true);
AddSlideAndText(outputPath, "PP-04 Open XML SDK PoC", "Reused source slide layout and theme.");
var outputInventory = InspectPresentation(outputPath);
var preservation = CompareMasterLayoutThemeParts(fixturePath, outputPath);
var validation = Validate(outputPath);

var invalidPath = Path.Combine(artifacts, "invalid-truncated.pptx");
var fixtureBytes = File.ReadAllBytes(fixturePath);
File.WriteAllBytes(invalidPath, fixtureBytes.Take(Math.Min(64, fixtureBytes.Length)).ToArray());
var invalidInput = TryOpenInvalid(invalidPath);

var unknownPartTest = RunUnknownPartPreservationTest(fixturePath, artifacts);

var report = new
{
    report_type = "PowerPointBackendPocReport",
    report_status = "partial",
    route_id = RouteId,
    task_id = TaskId,
    candidate = new
    {
        library = "DocumentFormat.OpenXml",
        package_version = "3.5.1",
        package_license = "MIT",
        product_backend_selected = false
    },
    environment = new
    {
        execution_location = "isolated Docker SDK container",
        container_image = Environment.GetEnvironmentVariable("YPP_POC_IMAGE") ?? "mcr.microsoft.com/dotnet/sdk:10.0",
        runtime_version = Environment.Version.ToString(),
        dotnet_sdk_version = Environment.GetEnvironmentVariable("YPP_DOTNET_SDK_VERSION") ?? "see container command output",
        product_runtime_selected = false
    },
    source = new
    {
        repository = "scanny/python-pptx",
        revision = SourceRevision,
        sample_path = "src/pptx/templates/default.pptx",
        license = "MIT",
        sha256 = fixtureHash
    },
    input_inventory = inputInventory,
    normal_case = new
    {
        status = outputInventory.SlidePartCount == 1 && outputInventory.MasterCount == inputInventory.MasterCount && outputInventory.LayoutCount == inputInventory.LayoutCount && outputInventory.ThemeCount == inputInventory.ThemeCount ? "passed" : "failed",
        output_file = "artifacts/pp04-output.pptx",
        output_sha256 = Sha256File(outputPath),
        output_inventory = outputInventory,
        master_layout_theme_parts_byte_identical = preservation.all_equal,
        changed_preservation_parts = preservation.differences,
        text_written = "PP-04 Open XML SDK PoC",
        placeholder_types_written = new[] { "title", "body" },
        text_runs_written = 2,
        reused_layout_ref = outputInventory.FirstSlideLayoutRef
    },
    unknown_part_preservation = unknownPartTest,
    validation = new
    {
        validator = "DocumentFormat.OpenXml.OpenXmlValidator",
        target = "Office2019",
        source_error_count = Validate(fixturePath).ErrorCount,
        output_error_count = validation.ErrorCount,
        output_errors = validation.Errors
    },
    boundary_case = new
    {
        status = inputInventory.SlidePartCount == 0 ? "observed" : "not_applicable",
        detail = "The fixed source package has master/layout/theme parts but no slide parts; the PoC added exactly one slide."
    },
    failure_case = invalidInput,
    capability_observations = new
    {
        create_open_save = "partial",
        add_slide_and_text = "partial",
        reuse_master_layout_theme = outputInventory.MasterCount == inputInventory.MasterCount && outputInventory.LayoutCount == inputInventory.LayoutCount && outputInventory.ThemeCount == inputInventory.ThemeCount && outputInventory.FirstSlideLayoutRef is not null ? "partial" : "failed",
        master_layout_theme_part_bytes_identical = preservation.all_equal,
        unknown_part_preservation = unknownPartTest.Status,
        image_table_chart_notes_comments_transitions_animations = "untested",
        rendering = "untested",
        emu_geometry = "not exercised"
    },
    limitations = new[]
    {
        "This is a candidate-backend PoC, not a YoloongPPT product runtime or architecture decision.",
        "The generated slide is structurally validated but not rendered by PowerPoint or LibreOffice.",
        "Two slide layout XML part hashes changed during SDK serialization; semantic equality was not separately tested, so exact template layout round-trip preservation is not claimed.",
        "Image/table/chart/notes/comments/transition/animation authoring and mutation were not exercised."
    }
};

var reportPath = Path.Combine(artifacts, "report.json");
await File.WriteAllTextAsync(reportPath, JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true, PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower }), new UTF8Encoding(false));
Console.WriteLine(JsonSerializer.Serialize(new
{
    route_id = RouteId,
    task_id = TaskId,
    report_status = "partial",
    input_inventory = inputInventory,
    output_inventory = outputInventory,
    master_layout_theme_parts_byte_identical = preservation.all_equal,
    unknown_part_preservation = unknownPartTest.Status,
    validation_error_count = validation.ErrorCount,
    failure_case = invalidInput.Status,
    report_path = reportPath
}, new JsonSerializerOptions { WriteIndented = true, PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower }));

static void AddSlideAndText(string path, string title, string body)
{
    using var document = PresentationDocument.Open(path, isEditable: true);
    var presentationPart = document.PresentationPart ?? throw new InvalidDataException("PresentationPart is missing.");
    var layouts = presentationPart.SlideMasterParts.SelectMany(master => master.SlideLayoutParts).ToArray();
    var layoutPart = layouts.FirstOrDefault(layout => layout.SlideLayout?.Type?.Value == P.SlideLayoutValues.Title) ?? layouts.FirstOrDefault();
    if (layoutPart is null)
    {
        throw new InvalidDataException("The source presentation has no slide layout part.");
    }

    var slidePart = presentationPart.AddNewPart<SlidePart>();
    slidePart.AddPart(layoutPart);
    slidePart.Slide = new P.Slide(
        new P.CommonSlideData(
            new P.ShapeTree(
                new P.NonVisualGroupShapeProperties(
                    new P.NonVisualDrawingProperties { Id = 1U, Name = string.Empty },
                    new P.NonVisualGroupShapeDrawingProperties(),
                    new P.ApplicationNonVisualDrawingProperties()),
                new P.GroupShapeProperties(
                    new A.TransformGroup(
                        new A.Offset { X = 0L, Y = 0L },
                        new A.Extents { Cx = 0L, Cy = 0L },
                        new A.ChildOffset { X = 0L, Y = 0L },
                        new A.ChildExtents { Cx = 0L, Cy = 0L })),
                MakePlaceholderShape(2U, "Title 1", P.PlaceholderValues.Title, title),
                MakePlaceholderShape(3U, "Content Placeholder 2", P.PlaceholderValues.Body, body))),
        new P.ColorMapOverride(new A.MasterColorMapping()));
    slidePart.Slide.Save();

    var presentation = presentationPart.Presentation ?? throw new InvalidDataException("Presentation root is missing.");
    var slideIdList = presentation.SlideIdList;
    if (slideIdList is null)
    {
        slideIdList = new P.SlideIdList();
        presentation.SlideIdList = slideIdList;
    }

    var maxId = slideIdList.Elements<P.SlideId>().Select(slideId => (uint?)slideId.Id?.Value).Where(value => value.HasValue).Select(value => value!.Value).DefaultIfEmpty(255U).Max();
    var nextId = Math.Max(256U, maxId + 1U);
    slideIdList.Append(new P.SlideId { Id = nextId, RelationshipId = presentationPart.GetIdOfPart(slidePart) });
    presentation.Save();
}

static P.Shape MakePlaceholderShape(uint id, string name, P.PlaceholderValues placeholder, string text)
{
    return new P.Shape(
        new P.NonVisualShapeProperties(
            new P.NonVisualDrawingProperties { Id = id, Name = name },
            new P.NonVisualShapeDrawingProperties(),
            new P.ApplicationNonVisualDrawingProperties(new P.PlaceholderShape { Type = placeholder })),
        new P.ShapeProperties(),
        new P.TextBody(
            new A.BodyProperties(),
            new A.ListStyle(),
            new A.Paragraph(
                new A.Run(new A.RunProperties(), new A.Text(text)),
                new A.EndParagraphRunProperties())));
}

static PresentationInventory InspectPresentation(string path)
{
    using var document = PresentationDocument.Open(path, isEditable: false);
    var presentationPart = document.PresentationPart ?? throw new InvalidDataException("PresentationPart is missing.");
    var masters = presentationPart.SlideMasterParts.ToArray();
    var layouts = masters.SelectMany(master => master.SlideLayoutParts).ToArray();
    var themes = masters.Select(master => master.ThemePart).OfType<ThemePart>().ToArray();
    var slides = presentationPart.SlideParts.ToArray();
    var firstSlide = slides.FirstOrDefault();
    var firstLayoutId = firstSlide is null ? null : firstSlide.SlideLayoutPart?.Uri.ToString();
    return new PresentationInventory(
        masters.Length,
        layouts.Length,
        themes.Length,
        slides.Length,
        firstLayoutId,
        new Dictionary<string, int>
        {
            ["masters"] = masters.Length,
            ["layouts"] = layouts.Length,
            ["themes"] = themes.Length,
            ["slides"] = slides.Length
        });
}

static (bool all_equal, string[] differences) CompareMasterLayoutThemeParts(string source, string output)
{
    var before = HashSelectedParts(source);
    var after = HashSelectedParts(output);
    var names = before.Keys.Union(after.Keys, StringComparer.Ordinal).OrderBy(name => name, StringComparer.Ordinal);
    var differences = names.Where(name => !before.TryGetValue(name, out var oldHash) || !after.TryGetValue(name, out var newHash) || !oldHash.Equals(newHash, StringComparison.OrdinalIgnoreCase)).ToArray();
    return (differences.Length == 0 && before.Count > 0, differences);
}

static Dictionary<string, string> HashSelectedParts(string path)
{
    using var file = File.OpenRead(path);
    using var archive = new ZipArchive(file, ZipArchiveMode.Read);
    var selected = archive.Entries.Where(entry =>
        entry.FullName.StartsWith("ppt/slideMasters/", StringComparison.Ordinal) ||
        entry.FullName.StartsWith("ppt/slideLayouts/", StringComparison.Ordinal) ||
        entry.FullName.StartsWith("ppt/theme/", StringComparison.Ordinal));
    return selected.ToDictionary(entry => entry.FullName, entry => HashEntry(entry), StringComparer.Ordinal);
}

static string HashEntry(ZipArchiveEntry entry)
{
    using var stream = entry.Open();
    return Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
}

static ValidationResult Validate(string path)
{
    using var document = PresentationDocument.Open(path, isEditable: false);
    var errors = new OpenXmlValidator(FileFormatVersions.Office2019)
        .Validate(document)
        .Take(20)
        .Select(error => $"{error.ErrorType}: {error.Description} ({error.Path?.XPath})")
        .ToArray();
    return new ValidationResult(errors.Length, errors);
}

static InvalidInputResult TryOpenInvalid(string path)
{
    try
    {
        using var document = PresentationDocument.Open(path, isEditable: false);
        return new InvalidInputResult("unexpectedly_opened", null, null);
    }
    catch (Exception exception)
    {
        return new InvalidInputResult("failed_as_expected", exception.GetType().FullName, exception.Message);
    }
}

static string Sha256File(string path)
{
    using var stream = File.OpenRead(path);
    return Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
}

static UnknownPartResult RunUnknownPartPreservationTest(string fixture, string artifactDirectory)
{
    const string unknownPartName = "ppt/yoloongppt/poc-unknown.xml";
    const string unknownXml = "<yoloongppt:unknown xmlns:yoloongppt=\"urn:yoloongppt:poc\">keep-this-part</yoloongppt:unknown>";
    var input = Path.Combine(artifactDirectory, "unknown-part-input.pptx");
    var output = Path.Combine(artifactDirectory, "unknown-part-output.pptx");
    var expectedHash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(unknownXml))).ToLowerInvariant();

    try
    {
        File.Copy(fixture, input, overwrite: true);
        InjectUnknownPart(input, unknownPartName, unknownXml);
        File.Copy(input, output, overwrite: true);
        AddSlideAndText(output, "Unknown part preservation", "The unrelated package part should remain byte-identical.");
        var actualHash = HashZipEntry(output, unknownPartName);
        var passed = actualHash.Equals(expectedHash, StringComparison.OrdinalIgnoreCase);
        return new UnknownPartResult(
            passed ? "passed" : "not_preserved",
            "artifacts/unknown-part-input.pptx",
            "artifacts/unknown-part-output.pptx",
            unknownPartName,
            expectedHash,
            actualHash);
    }
    catch (Exception exception)
    {
        return new UnknownPartResult(
            "failed",
            "artifacts/unknown-part-input.pptx",
            "artifacts/unknown-part-output.pptx",
            unknownPartName,
            expectedHash,
            null,
            exception.GetType().FullName,
            exception.Message);
    }
}

static void InjectUnknownPart(string path, string partName, string xml)
{
    const string contentTypesNamespace = "http://schemas.openxmlformats.org/package/2006/content-types";
    const string relationshipsNamespace = "http://schemas.openxmlformats.org/package/2006/relationships";
    using var archiveFile = File.Open(path, FileMode.Open, FileAccess.ReadWrite, FileShare.None);
    using var archive = new ZipArchive(archiveFile, ZipArchiveMode.Update);

    var contentTypes = LoadXmlEntry(archive, "[Content_Types].xml");
    var ctNs = XNamespace.Get(contentTypesNamespace);
    contentTypes.Root!.Add(new XElement(ctNs + "Override",
        new XAttribute("PartName", "/" + partName),
        new XAttribute("ContentType", "application/vnd.yoloongppt.poc-unknown+xml")));
    ReplaceXmlEntry(archive, "[Content_Types].xml", contentTypes);

    var rootRelationships = LoadXmlEntry(archive, "_rels/.rels");
    var relNs = XNamespace.Get(relationshipsNamespace);
    rootRelationships.Root!.Add(new XElement(relNs + "Relationship",
        new XAttribute("Id", "rIdYoloongPocUnknown"),
        new XAttribute("Type", "urn:yoloongppt:poc:unknown-part"),
        new XAttribute("Target", partName)));
    ReplaceXmlEntry(archive, "_rels/.rels", rootRelationships);

    var part = archive.CreateEntry(partName, CompressionLevel.Optimal);
    using var writer = new StreamWriter(part.Open(), new UTF8Encoding(false));
    writer.Write(xml);
}

static XDocument LoadXmlEntry(ZipArchive archive, string name)
{
    var entry = archive.GetEntry(name) ?? throw new InvalidDataException($"Missing package entry {name}.");
    using var stream = entry.Open();
    return XDocument.Load(stream, LoadOptions.PreserveWhitespace);
}

static void ReplaceXmlEntry(ZipArchive archive, string name, XDocument document)
{
    archive.GetEntry(name)?.Delete();
    var replacement = archive.CreateEntry(name, CompressionLevel.Optimal);
    using var stream = replacement.Open();
    document.Save(stream, SaveOptions.DisableFormatting);
}

static string HashZipEntry(string path, string partName)
{
    using var file = File.OpenRead(path);
    using var archive = new ZipArchive(file, ZipArchiveMode.Read);
    var entry = archive.GetEntry(partName) ?? throw new InvalidDataException($"Package part {partName} was dropped.");
    return HashEntry(entry);
}

internal sealed record PresentationInventory(
    int MasterCount,
    int LayoutCount,
    int ThemeCount,
    int SlidePartCount,
    string? FirstSlideLayoutRef,
    Dictionary<string, int> PartCounts);

internal sealed record ValidationResult(int ErrorCount, string[] Errors);

internal sealed record InvalidInputResult(string Status, string? ExceptionType, string? Message);

internal sealed record UnknownPartResult(
    string Status,
    string InputFile,
    string OutputFile,
    string PartName,
    string ExpectedSha256,
    string? ActualSha256,
    string? ExceptionType = null,
    string? Message = null);
