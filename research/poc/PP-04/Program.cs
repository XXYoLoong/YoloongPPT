using System.IO.Compression;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Xml.Linq;
using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Validation;
using A = DocumentFormat.OpenXml.Drawing;
using C = DocumentFormat.OpenXml.Drawing.Charts;
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
var semanticPreservation = CompareMasterLayoutThemePartsSemantically(fixturePath, outputPath);
var validation = Validate(outputPath);
var existingShapeMutation = RunExistingShapeMutation(fixturePath, artifacts);
var imageRoundTrip = RunImageRoundTrip(fixturePath, artifacts);
var tableRoundTrip = RunTableRoundTrip(fixturePath, artifacts);
var chartRoundTrip = RunChartRoundTrip(fixturePath, artifacts);

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
        sha256 = fixtureHash,
        poc_program_sha256 = Sha256File(Path.Combine(projectRoot, "Program.cs"))
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
        master_layout_theme_parts_semantically_equal = semanticPreservation.all_equal,
        semantically_changed_preservation_parts = semanticPreservation.differences,
        text_written = "PP-04 Open XML SDK PoC",
        placeholder_types_written = new[] { "title", "body" },
        text_runs_written = 2,
        reused_layout_ref = outputInventory.FirstSlideLayoutRef
    },
    existing_deck_mutation = existingShapeMutation,
    image_round_trip = imageRoundTrip,
    table_round_trip = tableRoundTrip,
    chart_round_trip = chartRoundTrip,
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
        master_layout_theme_parts_semantically_equal = semanticPreservation.all_equal,
        existing_shape_text_read_update = existingShapeMutation.Status,
        shape_geometry_emu_round_trip = existingShapeMutation.GeometryPreserved,
        autoshape_rectangle_fill_stroke = existingShapeMutation.Status,
        embedded_image_add_replace_read = imageRoundTrip.Status,
        table_cell_text_read_update = tableRoundTrip.Status,
        native_chart_series_data_read_update = chartRoundTrip.Status,
        unknown_part_preservation = unknownPartTest.Status,
        combo_error_bars_date_axis_notes_comments_transitions_animations_media = "untested",
        rendering = "untested"
    },
    limitations = new[]
    {
        "This is a candidate-backend PoC, not a YoloongPPT product runtime or architecture decision.",
        "The generated slide is structurally validated but not rendered by PowerPoint or LibreOffice.",
        "Two slide layout XML part hashes changed during SDK serialization; the selected master/layout/theme parts were XML-structure-equivalent after normalizing namespace declarations, attribute order, and insignificant formatting whitespace.",
        "The editable-shape case mutates a shape created earlier in this PoC; editing a pre-populated third-party slide was not exercised.",
        "Only a rectangle with fixed fill/stroke and explicit EMU geometry was exercised; other AutoShape types, adjustments, and rotation remain untested.",
        "The image case adds and replaces an embedded 1x1 PNG, then reopens and verifies its relationship, binary hash, alt text, and EMU bounds. Crop, contain/cover, rotation, transparency, compression, linked images, rendering, and broader image compatibility remain untested.",
        "The table case creates and updates text in one 2x2 table created by this PoC; cell formatting, merges, row/column editing, rendering, and third-party table mutation remain untested.",
        "The chart case creates one clustered column chart with one series, three categories, cached data and an embedded workbook; it updates one value in both the embedded workbook and chart cache. Combo charts, error bars, date axes, labels beyond value labels, rendering, and third-party chart mutation remain untested.",
        "Notes/comments/transition/animation/media authoring and mutation were not exercised."
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
    master_layout_theme_parts_semantically_equal = semanticPreservation.all_equal,
    existing_shape_mutation = existingShapeMutation.Status,
    image_round_trip = imageRoundTrip.Status,
    table_round_trip = tableRoundTrip.Status,
    chart_round_trip = chartRoundTrip.Status,
    unknown_part_preservation = unknownPartTest.Status,
    validation_error_count = validation.ErrorCount,
    mutation_validation_error_count = existingShapeMutation.ValidatorErrorCount,
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

static (bool all_equal, string[] differences) CompareMasterLayoutThemePartsSemantically(string source, string output)
{
    var before = CanonicalSelectedParts(source);
    var after = CanonicalSelectedParts(output);
    var names = before.Keys.Union(after.Keys, StringComparer.Ordinal).OrderBy(name => name, StringComparer.Ordinal);
    var differences = names.Where(name => !before.TryGetValue(name, out var oldValue) || !after.TryGetValue(name, out var newValue) || !oldValue.Equals(newValue, StringComparison.Ordinal)).ToArray();
    return (differences.Length == 0 && before.Count > 0, differences);
}

static Dictionary<string, string> CanonicalSelectedParts(string path)
{
    using var file = File.OpenRead(path);
    using var archive = new ZipArchive(file, ZipArchiveMode.Read);
    var selected = archive.Entries.Where(entry =>
        entry.FullName.StartsWith("ppt/slideMasters/", StringComparison.Ordinal) ||
        entry.FullName.StartsWith("ppt/slideLayouts/", StringComparison.Ordinal) ||
        entry.FullName.StartsWith("ppt/theme/", StringComparison.Ordinal));
    return selected.ToDictionary(entry => entry.FullName, entry => CanonicalizeXmlEntry(entry), StringComparer.Ordinal);
}

static string CanonicalizeXmlEntry(ZipArchiveEntry entry)
{
    using var stream = entry.Open();
    var document = XDocument.Load(stream, LoadOptions.None);
    var root = document.Root ?? throw new InvalidDataException($"XML part {entry.FullName} has no root element.");
    var builder = new StringBuilder();
    AppendCanonicalElement(builder, root);
    return builder.ToString();
}

static void AppendCanonicalElement(StringBuilder builder, XElement element)
{
    builder.Append('<').Append(ExpandedName(element.Name));
    foreach (var attribute in element.Attributes()
                 .Where(attribute => !attribute.IsNamespaceDeclaration)
                 .OrderBy(attribute => attribute.Name.NamespaceName, StringComparer.Ordinal)
                 .ThenBy(attribute => attribute.Name.LocalName, StringComparer.Ordinal))
    {
        builder.Append(' ').Append(ExpandedName(attribute.Name)).Append('=')
            .Append(JsonSerializer.Serialize(attribute.Value));
    }

    builder.Append('>');
    foreach (var node in element.Nodes())
    {
        if (node is XElement child)
        {
            AppendCanonicalElement(builder, child);
        }
        else if (node is XText text)
        {
            builder.Append("T").Append(JsonSerializer.Serialize(text.Value));
        }
    }

    builder.Append("</").Append(ExpandedName(element.Name)).Append('>');
}

static string ExpandedName(XName name) => $"{{{name.NamespaceName}}}{name.LocalName}";

static ShapeMutationResult RunExistingShapeMutation(string fixture, string artifactDirectory)
{
    const string shapeName = "YoloongPPT Editable Probe";
    const string beforeText = "Existing shape before edit";
    const string afterText = "Existing shape after edit";
    const long expectedX = 914400L;
    const long expectedY = 457200L;
    const long expectedCx = 3657600L;
    const long expectedCy = 1828800L;
    var output = Path.Combine(artifactDirectory, "existing-shape-mutation.pptx");
    File.Copy(fixture, output, overwrite: true);
    AddSlideAndText(output, "Existing deck mutation", "The next shape is modified after the first save.");
    AddEditableProbeShape(output, shapeName, beforeText, expectedX, expectedY, expectedCx, expectedCy);

    var before = ReadShapeSnapshot(output, shapeName);
    UpdateShapeText(output, shapeName, afterText);
    var after = ReadShapeSnapshot(output, shapeName);
    var validation = Validate(output);
    var geometryPreserved = before.ShapeId == after.ShapeId &&
        before.Name == after.Name &&
        before.X == after.X && before.Y == after.Y &&
        before.Cx == after.Cx && before.Cy == after.Cy &&
        before.PresetGeometry == after.PresetGeometry &&
        before.FillColor == after.FillColor &&
        before.OutlineColor == after.OutlineColor &&
        after.X == expectedX && after.Y == expectedY &&
        after.Cx == expectedCx && after.Cy == expectedCy &&
        after.PresetGeometry == "rect" &&
        after.FillColor == "4472C4" &&
        after.OutlineColor == "1F1F1F";
    var textUpdated = before.Text == beforeText && after.Text == afterText;
    var status = geometryPreserved && textUpdated && validation.ErrorCount == 0 ? "passed" : "failed";

    return new ShapeMutationResult(
        status,
        "The probe shape is created and saved by this PoC, then the deck is reopened and the same shape's text is changed; this is not a foreign populated template test.",
        "fixtures/python-pptx-default.pptx",
        "artifacts/existing-shape-mutation.pptx",
        Sha256File(output),
        shapeName,
        before,
        after,
        geometryPreserved,
        textUpdated,
        validation.ErrorCount,
        validation.Errors);
}

static void AddEditableProbeShape(string path, string name, string text, long x, long y, long cx, long cy)
{
    using var document = PresentationDocument.Open(path, isEditable: true);
    var slidePart = document.PresentationPart?.SlideParts.SingleOrDefault()
        ?? throw new InvalidDataException("Expected exactly one slide for the existing-shape mutation case.");
    var slide = slidePart.Slide ?? throw new InvalidDataException("Slide root is missing from the mutation part.");
    var shapeTree = slide.CommonSlideData?.ShapeTree
        ?? throw new InvalidDataException("ShapeTree is missing from the mutation slide.");
    shapeTree.Append(new P.Shape(
        new P.NonVisualShapeProperties(
            new P.NonVisualDrawingProperties { Id = 4U, Name = name },
            new P.NonVisualShapeDrawingProperties(),
            new P.ApplicationNonVisualDrawingProperties()),
        new P.ShapeProperties(
            new A.Transform2D(
                new A.Offset { X = x, Y = y },
                new A.Extents { Cx = cx, Cy = cy }),
            new A.PresetGeometry(new A.AdjustValueList()) { Preset = A.ShapeTypeValues.Rectangle },
            new A.SolidFill(new A.RgbColorModelHex { Val = "4472C4" }),
            new A.Outline(new A.SolidFill(new A.RgbColorModelHex { Val = "1F1F1F" }))),
        new P.TextBody(
            new A.BodyProperties(),
            new A.ListStyle(),
            new A.Paragraph(
                new A.Run(new A.RunProperties(), new A.Text(text)),
                new A.EndParagraphRunProperties()))));
    slide.Save();
}

static ShapeSnapshot ReadShapeSnapshot(string path, string name)
{
    using var document = PresentationDocument.Open(path, isEditable: false);
    var slidePart = document.PresentationPart?.SlideParts.SingleOrDefault()
        ?? throw new InvalidDataException("Expected exactly one slide for the existing-shape mutation case.");
    var slide = slidePart.Slide ?? throw new InvalidDataException("Slide root is missing from the mutation part.");
    var shape = slide.CommonSlideData?.ShapeTree?.Elements<P.Shape>()
        .SingleOrDefault(candidate => candidate.NonVisualShapeProperties?.NonVisualDrawingProperties?.Name?.Value == name)
        ?? throw new InvalidDataException($"Shape {name} was not found.");
    var transform = shape.ShapeProperties?.GetFirstChild<A.Transform2D>();
    var presetGeometry = shape.ShapeProperties?.GetFirstChild<A.PresetGeometry>();
    var geometry = presetGeometry?.GetAttribute("prst", string.Empty).Value;
    var fillColor = shape.ShapeProperties?.GetFirstChild<A.SolidFill>()?.GetFirstChild<A.RgbColorModelHex>()?.Val?.Value;
    var outlineColor = shape.ShapeProperties?.GetFirstChild<A.Outline>()?.GetFirstChild<A.SolidFill>()
        ?.GetFirstChild<A.RgbColorModelHex>()?.Val?.Value;
    var text = string.Concat(shape.TextBody?.Descendants<A.Text>().Select(run => run.Text) ?? []);
    return new ShapeSnapshot(
        shape.NonVisualShapeProperties?.NonVisualDrawingProperties?.Id?.Value,
        shape.NonVisualShapeProperties?.NonVisualDrawingProperties?.Name?.Value,
        transform?.Offset?.X?.Value,
        transform?.Offset?.Y?.Value,
        transform?.Extents?.Cx?.Value,
        transform?.Extents?.Cy?.Value,
        geometry,
        fillColor,
        outlineColor,
        text);
}

static void UpdateShapeText(string path, string name, string text)
{
    using var document = PresentationDocument.Open(path, isEditable: true);
    var slidePart = document.PresentationPart?.SlideParts.SingleOrDefault()
        ?? throw new InvalidDataException("Expected exactly one slide for the existing-shape mutation case.");
    var slide = slidePart.Slide ?? throw new InvalidDataException("Slide root is missing from the mutation part.");
    var shape = slide.CommonSlideData?.ShapeTree?.Elements<P.Shape>()
        .SingleOrDefault(candidate => candidate.NonVisualShapeProperties?.NonVisualDrawingProperties?.Name?.Value == name)
        ?? throw new InvalidDataException($"Shape {name} was not found.");
    var textElement = shape.TextBody?.Descendants<A.Text>().FirstOrDefault()
        ?? throw new InvalidDataException($"Shape {name} contains no editable text run.");
    textElement.Text = text;
    slide.Save();
}

static ImageRoundTripResult RunImageRoundTrip(string fixture, string artifactDirectory)
{
    const string imageName = "YoloongPPT Embedded Image Probe";
    const string altText = "One-pixel embedded PNG used to verify image relationships and replacement.";
    const long expectedX = 914400L;
    const long expectedY = 457200L;
    const long expectedCx = 1828800L;
    const long expectedCy = 914400L;
    var originalBytes = Convert.FromBase64String("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=");
    var replacementBytes = Convert.FromBase64String("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADUlEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC");
    var output = Path.Combine(artifactDirectory, "image-roundtrip.pptx");
    File.Copy(fixture, output, overwrite: true);
    AddSlideAndText(output, "Embedded image round trip", "The embedded PNG is replaced after the first save.");
    AddEmbeddedImage(output, imageName, altText, originalBytes, expectedX, expectedY, expectedCx, expectedCy);

    var before = ReadImageSnapshot(output, imageName);
    ReplaceEmbeddedImage(output, imageName, replacementBytes);
    var after = ReadImageSnapshot(output, imageName);
    var validation = Validate(output);
    var boundsPreserved = before.X == after.X && before.Y == after.Y &&
        before.Cx == after.Cx && before.Cy == after.Cy &&
        after.X == expectedX && after.Y == expectedY &&
        after.Cx == expectedCx && after.Cy == expectedCy;
    var identityPreserved = before.ShapeId == after.ShapeId &&
        before.Name == after.Name && before.AltText == after.AltText &&
        before.RelationshipId == after.RelationshipId;
    var imageReplaced = before.ImageSha256 == Sha256Bytes(originalBytes) &&
        after.ImageSha256 == Sha256Bytes(replacementBytes) &&
        before.ImageSha256 != after.ImageSha256 &&
        after.ContentType == "image/png";
    var status = boundsPreserved && identityPreserved && imageReplaced && validation.ErrorCount == 0 ? "passed" : "failed";

    return new ImageRoundTripResult(
        status,
        "A 1x1 PNG is embedded by this PoC, then replaced in place; this does not exercise crop/render behavior or a third-party image object.",
        "fixtures/python-pptx-default.pptx",
        "artifacts/image-roundtrip.pptx",
        Sha256File(output),
        imageName,
        altText,
        Sha256Bytes(originalBytes),
        Sha256Bytes(replacementBytes),
        before,
        after,
        boundsPreserved,
        identityPreserved,
        imageReplaced,
        validation.ErrorCount,
        validation.Errors);
}

static void AddEmbeddedImage(string path, string name, string altText, byte[] imageBytes, long x, long y, long cx, long cy)
{
    using var document = PresentationDocument.Open(path, isEditable: true);
    var slidePart = document.PresentationPart?.SlideParts.SingleOrDefault()
        ?? throw new InvalidDataException("Expected exactly one slide for the image round-trip case.");
    var slide = slidePart.Slide ?? throw new InvalidDataException("Slide root is missing from the image test part.");
    var shapeTree = slide.CommonSlideData?.ShapeTree
        ?? throw new InvalidDataException("ShapeTree is missing from the image test slide.");
    var imagePart = slidePart.AddImagePart(ImagePartType.Png);
    using (var imageStream = new MemoryStream(imageBytes, writable: false))
    {
        imagePart.FeedData(imageStream);
    }

    var relationshipId = slidePart.GetIdOfPart(imagePart);
    shapeTree.Append(new P.Picture(
        new P.NonVisualPictureProperties(
            new P.NonVisualDrawingProperties { Id = 4U, Name = name, Description = altText },
            new P.NonVisualPictureDrawingProperties(new A.PictureLocks { NoChangeAspect = true }),
            new P.ApplicationNonVisualDrawingProperties()),
        new P.BlipFill(
            new A.Blip { Embed = relationshipId },
            new A.Stretch(new A.FillRectangle())),
        new P.ShapeProperties(
            new A.Transform2D(
                new A.Offset { X = x, Y = y },
                new A.Extents { Cx = cx, Cy = cy }),
            new A.PresetGeometry(new A.AdjustValueList()) { Preset = A.ShapeTypeValues.Rectangle })));
    slide.Save();
}

static void ReplaceEmbeddedImage(string path, string name, byte[] replacementBytes)
{
    using var document = PresentationDocument.Open(path, isEditable: true);
    var slidePart = document.PresentationPart?.SlideParts.SingleOrDefault()
        ?? throw new InvalidDataException("Expected exactly one slide for the image replacement case.");
    var picture = slidePart.Slide?.CommonSlideData?.ShapeTree?.Elements<P.Picture>()
        .SingleOrDefault(candidate => candidate.NonVisualPictureProperties?.NonVisualDrawingProperties?.Name?.Value == name)
        ?? throw new InvalidDataException($"Picture {name} was not found.");
    var relationshipId = picture.BlipFill?.Blip?.Embed?.Value
        ?? throw new InvalidDataException($"Picture {name} has no embedded image relationship.");
    var imagePart = slidePart.GetPartById(relationshipId) as ImagePart
        ?? throw new InvalidDataException($"Picture {name} relationship does not resolve to an ImagePart.");
    using var replacementStream = new MemoryStream(replacementBytes, writable: false);
    imagePart.FeedData(replacementStream);
}

static ImageSnapshot ReadImageSnapshot(string path, string name)
{
    using var document = PresentationDocument.Open(path, isEditable: false);
    var slidePart = document.PresentationPart?.SlideParts.SingleOrDefault()
        ?? throw new InvalidDataException("Expected exactly one slide for the image snapshot case.");
    var picture = slidePart.Slide?.CommonSlideData?.ShapeTree?.Elements<P.Picture>()
        .SingleOrDefault(candidate => candidate.NonVisualPictureProperties?.NonVisualDrawingProperties?.Name?.Value == name)
        ?? throw new InvalidDataException($"Picture {name} was not found.");
    var drawingProperties = picture.NonVisualPictureProperties?.NonVisualDrawingProperties
        ?? throw new InvalidDataException($"Picture {name} has no non-visual drawing properties.");
    var transform = picture.ShapeProperties?.GetFirstChild<A.Transform2D>()
        ?? throw new InvalidDataException($"Picture {name} has no geometry transform.");
    var relationshipId = picture.BlipFill?.Blip?.Embed?.Value
        ?? throw new InvalidDataException($"Picture {name} has no embedded image relationship.");
    var imagePart = slidePart.GetPartById(relationshipId) as ImagePart
        ?? throw new InvalidDataException($"Picture {name} relationship does not resolve to an ImagePart.");
    using var imageStream = imagePart.GetStream(FileMode.Open, FileAccess.Read);
    var imageSha256 = Convert.ToHexString(SHA256.HashData(imageStream)).ToLowerInvariant();

    return new ImageSnapshot(
        drawingProperties.Id?.Value,
        drawingProperties.Name?.Value,
        drawingProperties.Description?.Value,
        relationshipId,
        imagePart.ContentType,
        imageSha256,
        transform.Offset?.X?.Value,
        transform.Offset?.Y?.Value,
        transform.Extents?.Cx?.Value,
        transform.Extents?.Cy?.Value);
}

static string Sha256Bytes(byte[] bytes) => Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();

static TableRoundTripResult RunTableRoundTrip(string fixture, string artifactDirectory)
{
    const string tableName = "YoloongPPT Editable Table Probe";
    const long expectedX = 457200L;
    const long expectedY = 914400L;
    const long expectedCx = 4572000L;
    const long expectedCy = 1828800L;
    const string updatedCellText = "ReadUpdatePassed";
    var expectedCellsBefore = new[]
    {
        new[] { "Header", "Status" },
        new[] { "PPT-016", "Pending" }
    };
    var output = Path.Combine(artifactDirectory, "table-roundtrip.pptx");
    File.Copy(fixture, output, overwrite: true);
    AddSlideAndText(output, "Table round trip", "The 2x2 table cell text is updated after the first save.");
    AddEditableProbeTable(output, tableName, expectedCellsBefore, expectedX, expectedY, expectedCx, expectedCy);

    var before = ReadTableSnapshot(output, tableName);
    UpdateTableCellText(output, tableName, rowIndex: 1, columnIndex: 1, updatedCellText);
    var after = ReadTableSnapshot(output, tableName);
    var validation = Validate(output);
    var identityAndGeometryPreserved = before.ShapeId == after.ShapeId && before.Name == after.Name &&
        before.X == after.X && before.Y == after.Y && before.Cx == after.Cx && before.Cy == after.Cy &&
        after.X == expectedX && after.Y == expectedY && after.Cx == expectedCx && after.Cy == expectedCy;
    var tableDimensionsPreserved = before.RowCount == 2 && before.ColumnCount == 2 &&
        after.RowCount == before.RowCount && after.ColumnCount == before.ColumnCount;
    var textUpdated = before.Cells.SelectMany(cells => cells).SequenceEqual(expectedCellsBefore.SelectMany(cells => cells)) &&
        after.Cells.Length == 2 && after.Cells.All(row => row.Length == 2) &&
        after.Cells[0].SequenceEqual(expectedCellsBefore[0]) &&
        after.Cells[1][0] == expectedCellsBefore[1][0] &&
        after.Cells[1][1] == updatedCellText;
    var status = identityAndGeometryPreserved && tableDimensionsPreserved && textUpdated && validation.ErrorCount == 0
        ? "passed"
        : "failed";

    return new TableRoundTripResult(
        status,
        "This PoC creates a 2x2 table, saves and reopens the deck, updates one cell's text, then reads it back; table formatting and editing a third-party table are outside this case.",
        "fixtures/python-pptx-default.pptx",
        "artifacts/table-roundtrip.pptx",
        Sha256File(output),
        tableName,
        before,
        after,
        identityAndGeometryPreserved,
        tableDimensionsPreserved,
        textUpdated,
        validation.ErrorCount,
        validation.Errors);
}

static void AddEditableProbeTable(string path, string name, string[][] cells, long x, long y, long cx, long cy)
{
    using var document = PresentationDocument.Open(path, isEditable: true);
    var slidePart = document.PresentationPart?.SlideParts.SingleOrDefault()
        ?? throw new InvalidDataException("Expected exactly one slide for the table round-trip case.");
    var slide = slidePart.Slide ?? throw new InvalidDataException("Slide root is missing from the table test part.");
    var shapeTree = slide.CommonSlideData?.ShapeTree
        ?? throw new InvalidDataException("ShapeTree is missing from the table test slide.");
    if (cells.Length == 0 || cells.Any(row => row.Length != cells[0].Length) || cells[0].Length == 0)
    {
        throw new ArgumentException("The probe table must be a non-empty rectangular matrix.", nameof(cells));
    }

    var columnWidth = cx / cells[0].Length;
    var rowHeight = cy / cells.Length;
    var table = new A.Table(new A.TableProperties());
    var tableGrid = new A.TableGrid();
    for (var columnIndex = 0; columnIndex < cells[0].Length; columnIndex++)
    {
        tableGrid.AppendChild(new A.GridColumn { Width = columnWidth });
    }
    table.AppendChild(tableGrid);
    foreach (var cellTexts in cells)
    {
        var tableRow = new A.TableRow { Height = rowHeight };
        foreach (var cellText in cellTexts)
        {
            tableRow.AppendChild(MakeTableCell(cellText));
        }
        table.AppendChild(tableRow);
    }
    shapeTree.Append(new P.GraphicFrame(
        new P.NonVisualGraphicFrameProperties(
            new P.NonVisualDrawingProperties { Id = 4U, Name = name },
            new P.NonVisualGraphicFrameDrawingProperties(),
            new P.ApplicationNonVisualDrawingProperties()),
        new P.Transform(
            new A.Offset { X = x, Y = y },
            new A.Extents { Cx = cx, Cy = cy }),
        new A.Graphic(
            new A.GraphicData(table)
            {
                Uri = "http://schemas.openxmlformats.org/drawingml/2006/table"
            })));
    slide.Save();
}

static A.TableCell MakeTableCell(string text) => new(
    new A.TextBody(
        new A.BodyProperties(),
        new A.ListStyle(),
        new A.Paragraph(
            new A.Run(new A.RunProperties(), new A.Text(text)),
            new A.EndParagraphRunProperties())),
    new A.TableCellProperties());

static TableSnapshot ReadTableSnapshot(string path, string name)
{
    using var document = PresentationDocument.Open(path, isEditable: false);
    var slidePart = document.PresentationPart?.SlideParts.SingleOrDefault()
        ?? throw new InvalidDataException("Expected exactly one slide for the table snapshot case.");
    var slide = slidePart.Slide ?? throw new InvalidDataException("Slide root is missing from the table snapshot part.");
    var frame = slide.CommonSlideData?.ShapeTree?.Elements<P.GraphicFrame>()
        .SingleOrDefault(candidate => candidate.NonVisualGraphicFrameProperties?.NonVisualDrawingProperties?.Name?.Value == name)
        ?? throw new InvalidDataException($"Table graphic frame {name} was not found.");
    var table = frame.Graphic?.GraphicData?.GetFirstChild<A.Table>()
        ?? throw new InvalidDataException($"Table graphic frame {name} does not contain an a:tbl table.");
    var rows = table.Elements<A.TableRow>()
        .Select(row => row.Elements<A.TableCell>()
            .Select(cell => string.Concat(cell.TextBody?.Descendants<A.Text>().Select(text => text.Text) ?? []))
            .ToArray())
        .ToArray();
    var columns = table.TableGrid?.Elements<A.GridColumn>().Count() ?? 0;
    var transform = frame.Transform;
    return new TableSnapshot(
        frame.NonVisualGraphicFrameProperties?.NonVisualDrawingProperties?.Id?.Value,
        frame.NonVisualGraphicFrameProperties?.NonVisualDrawingProperties?.Name?.Value,
        transform?.Offset?.X?.Value,
        transform?.Offset?.Y?.Value,
        transform?.Extents?.Cx?.Value,
        transform?.Extents?.Cy?.Value,
        rows.Length,
        columns,
        rows);
}

static void UpdateTableCellText(string path, string name, int rowIndex, int columnIndex, string text)
{
    using var document = PresentationDocument.Open(path, isEditable: true);
    var slidePart = document.PresentationPart?.SlideParts.SingleOrDefault()
        ?? throw new InvalidDataException("Expected exactly one slide for the table update case.");
    var slide = slidePart.Slide ?? throw new InvalidDataException("Slide root is missing from the table update part.");
    var frame = slide.CommonSlideData?.ShapeTree?.Elements<P.GraphicFrame>()
        .SingleOrDefault(candidate => candidate.NonVisualGraphicFrameProperties?.NonVisualDrawingProperties?.Name?.Value == name)
        ?? throw new InvalidDataException($"Table graphic frame {name} was not found.");
    var table = frame.Graphic?.GraphicData?.GetFirstChild<A.Table>()
        ?? throw new InvalidDataException($"Table graphic frame {name} does not contain an a:tbl table.");
    var cell = table.Elements<A.TableRow>().ElementAt(rowIndex).Elements<A.TableCell>().ElementAt(columnIndex);
    var textElement = cell.TextBody?.Descendants<A.Text>().FirstOrDefault()
        ?? throw new InvalidDataException($"Table cell ({rowIndex},{columnIndex}) has no editable text run.");
    textElement.Text = text;
    slide.Save();
}

static ChartRoundTripResult RunChartRoundTrip(string fixture, string artifactDirectory)
{
    const string chartName = "YoloongPPT Native Chart Probe";
    const string updatedValue = "20";
    const long expectedX = 457200L;
    const long expectedY = 914400L;
    const long expectedCx = 4572000L;
    const long expectedCy = 2743200L;
    var output = Path.Combine(artifactDirectory, "chart-roundtrip.pptx");
    File.Copy(fixture, output, overwrite: true);
    AddSlideAndText(output, "Native chart round trip", "The embedded chart workbook and cached series value are updated together.");
    AddEditableProbeChart(output, chartName, expectedX, expectedY, expectedCx, expectedCy);

    var before = ReadChartSnapshot(output, chartName);
    UpdateChartValue(output, chartName, pointIndex: 1, updatedValue);
    var after = ReadChartSnapshot(output, chartName);
    var validation = Validate(output);
    var embeddedWorkbookValidation = ValidateEmbeddedWorkbook(output, chartName);
    var identityAndGeometryPreserved = before.ShapeId == after.ShapeId && before.Name == after.Name &&
        before.X == after.X && before.Y == after.Y && before.Cx == after.Cx && before.Cy == after.Cy &&
        after.X == expectedX && after.Y == expectedY && after.Cx == expectedCx && after.Cy == expectedCy;
    var chartDefinitionPreserved = before.ChartType == "barChart" && after.ChartType == before.ChartType &&
        before.Title == "Quarterly Revenue" && after.Title == before.Title &&
        before.SeriesName == "Revenue" && after.SeriesName == before.SeriesName &&
        before.Categories.SequenceEqual(new[] { "Q1", "Q2", "Q3" }) &&
        after.Categories.SequenceEqual(before.Categories) &&
        before.SeriesFormula == after.SeriesFormula && before.CategoryFormula == after.CategoryFormula &&
        before.ValuesFormula == after.ValuesFormula && before.AxisIds.SequenceEqual(after.AxisIds) &&
        before.HasLegend && after.HasLegend && before.HasValueLabels && after.HasValueLabels &&
        before.EmbeddedWorkbookRelationshipId == before.EmbeddedRelationshipId &&
        after.EmbeddedWorkbookRelationshipId == after.EmbeddedRelationshipId;
    var dataUpdated = before.Values.SequenceEqual(new[] { "12", "18", "15" }) &&
        after.Values.SequenceEqual(new[] { "12", updatedValue, "15" }) &&
        before.EmbeddedWorkbookValue == "18" && after.EmbeddedWorkbookValue == updatedValue &&
        before.EmbeddedWorkbookSha256 != after.EmbeddedWorkbookSha256;
    var status = identityAndGeometryPreserved && chartDefinitionPreserved && dataUpdated &&
        validation.ErrorCount == 0 && embeddedWorkbookValidation.ErrorCount == 0
        ? "passed"
        : "failed";

    return new ChartRoundTripResult(
        status,
        "This PoC creates one clustered column chart with one series, three categories, cached values, and an embedded workbook; it saves/reopens and updates one value in the cache and embedded workbook. Rendering and other chart types/features are outside this case.",
        "fixtures/python-pptx-default.pptx",
        "artifacts/chart-roundtrip.pptx",
        Sha256File(output),
        chartName,
        before,
        after,
        identityAndGeometryPreserved,
        chartDefinitionPreserved,
        dataUpdated,
        validation.ErrorCount,
        validation.Errors,
        embeddedWorkbookValidation.ErrorCount,
        embeddedWorkbookValidation.Errors);
}

static void AddEditableProbeChart(string path, string name, long x, long y, long cx, long cy)
{
    using var document = PresentationDocument.Open(path, isEditable: true);
    var slidePart = document.PresentationPart?.SlideParts.SingleOrDefault()
        ?? throw new InvalidDataException("Expected exactly one slide for the chart round-trip case.");
    var slide = slidePart.Slide ?? throw new InvalidDataException("Slide root is missing from the chart test part.");
    var shapeTree = slide.CommonSlideData?.ShapeTree
        ?? throw new InvalidDataException("ShapeTree is missing from the chart test slide.");
    var chartPart = slidePart.AddNewPart<ChartPart>();
    var workbookPart = chartPart.AddEmbeddedPackagePart(EmbeddedPackagePartType.Xlsx);
    var workbookBytes = CreateEmbeddedChartWorkbook();
    using (var workbookStream = new MemoryStream(workbookBytes, writable: false))
    {
        workbookPart.FeedData(workbookStream);
    }

    var workbookRelationshipId = chartPart.GetIdOfPart(workbookPart);
    var chartXml = $$"""
        <c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
          <c:lang val="en-US"/>
          <c:chart>
            <c:title><c:tx><c:rich><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US"/><a:t>Quarterly Revenue</a:t></a:r><a:endParaRPr lang="en-US"/></a:p></c:rich></c:tx><c:overlay val="0"/></c:title>
            <c:plotArea>
              <c:layout/>
              <c:barChart>
                <c:barDir val="col"/><c:grouping val="clustered"/><c:varyColors val="0"/>
                <c:ser>
                  <c:idx val="0"/><c:order val="0"/>
                  <c:tx><c:strRef><c:f>ChartData!$B$1</c:f><c:strCache><c:ptCount val="1"/><c:pt idx="0"><c:v>Revenue</c:v></c:pt></c:strCache></c:strRef></c:tx>
                  <c:invertIfNegative val="0"/>
                  <c:cat><c:strRef><c:f>ChartData!$A$2:$A$4</c:f><c:strCache><c:ptCount val="3"/><c:pt idx="0"><c:v>Q1</c:v></c:pt><c:pt idx="1"><c:v>Q2</c:v></c:pt><c:pt idx="2"><c:v>Q3</c:v></c:pt></c:strCache></c:strRef></c:cat>
                  <c:val><c:numRef><c:f>ChartData!$B$2:$B$4</c:f><c:numCache><c:formatCode>General</c:formatCode><c:ptCount val="3"/><c:pt idx="0"><c:v>12</c:v></c:pt><c:pt idx="1"><c:v>18</c:v></c:pt><c:pt idx="2"><c:v>15</c:v></c:pt></c:numCache></c:numRef></c:val>
                </c:ser>
                <c:dLbls><c:showLegendKey val="0"/><c:showVal val="1"/><c:showCatName val="0"/><c:showSerName val="0"/><c:showPercent val="0"/><c:showLeaderLines val="0"/></c:dLbls>
                <c:gapWidth val="150"/><c:overlap val="0"/><c:axId val="48650112"/><c:axId val="48672768"/>
              </c:barChart>
              <c:catAx><c:axId val="48650112"/><c:scaling><c:orientation val="minMax"/></c:scaling><c:delete val="0"/><c:axPos val="b"/><c:majorTickMark val="none"/><c:minorTickMark val="none"/><c:tickLblPos val="nextTo"/><c:crossAx val="48672768"/><c:crosses val="autoZero"/><c:auto val="1"/><c:lblAlgn val="ctr"/><c:lblOffset val="100"/></c:catAx>
              <c:valAx><c:axId val="48672768"/><c:scaling><c:orientation val="minMax"/></c:scaling><c:delete val="0"/><c:axPos val="l"/><c:numFmt formatCode="General" sourceLinked="1"/><c:majorTickMark val="none"/><c:minorTickMark val="none"/><c:tickLblPos val="nextTo"/><c:crossAx val="48650112"/><c:crosses val="autoZero"/><c:crossBetween val="between"/></c:valAx>
            </c:plotArea>
            <c:legend><c:legendPos val="r"/><c:overlay val="0"/></c:legend>
            <c:plotVisOnly val="1"/><c:dispBlanksAs val="gap"/>
          </c:chart>
          <c:externalData r:id="{{workbookRelationshipId}}"><c:autoUpdate val="0"/></c:externalData>
        </c:chartSpace>
        """;
    chartPart.ChartSpace = new C.ChartSpace(chartXml);
    chartPart.ChartSpace.Save();

    var chartRelationshipId = slidePart.GetIdOfPart(chartPart);
    shapeTree.Append(new P.GraphicFrame(
        new P.NonVisualGraphicFrameProperties(
            new P.NonVisualDrawingProperties { Id = 4U, Name = name },
            new P.NonVisualGraphicFrameDrawingProperties(),
            new P.ApplicationNonVisualDrawingProperties()),
        new P.Transform(
            new A.Offset { X = x, Y = y },
            new A.Extents { Cx = cx, Cy = cy }),
        new A.Graphic(
            new A.GraphicData(new C.ChartReference { Id = chartRelationshipId })
            {
                Uri = "http://schemas.openxmlformats.org/drawingml/2006/chart"
            })));
    slide.Save();
}

static byte[] CreateEmbeddedChartWorkbook()
{
    const string relationshipNamespace = "http://schemas.openxmlformats.org/package/2006/relationships";
    const string officeRelationshipNamespace = "http://schemas.openxmlformats.org/officeDocument/2006/relationships";
    const string spreadsheetNamespace = "http://schemas.openxmlformats.org/spreadsheetml/2006/main";
    const string contentTypesNamespace = "http://schemas.openxmlformats.org/package/2006/content-types";
    XNamespace rel = relationshipNamespace;
    XNamespace officeRel = officeRelationshipNamespace;
    XNamespace sheet = spreadsheetNamespace;
    XNamespace contentType = contentTypesNamespace;

    using var output = new MemoryStream();
    using (var archive = new ZipArchive(output, ZipArchiveMode.Create, leaveOpen: true))
    {
        WriteXmlEntry(archive, "[Content_Types].xml", new XDocument(
            new XElement(contentType + "Types",
                new XElement(contentType + "Default", new XAttribute("Extension", "rels"), new XAttribute("ContentType", "application/vnd.openxmlformats-package.relationships+xml")),
                new XElement(contentType + "Default", new XAttribute("Extension", "xml"), new XAttribute("ContentType", "application/xml")),
                new XElement(contentType + "Override", new XAttribute("PartName", "/xl/workbook.xml"), new XAttribute("ContentType", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml")),
                new XElement(contentType + "Override", new XAttribute("PartName", "/xl/worksheets/sheet1.xml"), new XAttribute("ContentType", "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml")))));
        WriteXmlEntry(archive, "_rels/.rels", new XDocument(
            new XElement(rel + "Relationships",
                new XElement(rel + "Relationship",
                    new XAttribute("Id", "rId1"),
                    new XAttribute("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"),
                    new XAttribute("Target", "xl/workbook.xml")))));
        WriteXmlEntry(archive, "xl/workbook.xml", new XDocument(
            new XElement(sheet + "workbook",
                new XAttribute(XNamespace.Xmlns + "r", officeRel),
                new XElement(sheet + "sheets",
                    new XElement(sheet + "sheet",
                        new XAttribute("name", "ChartData"),
                        new XAttribute("sheetId", "1"),
                        new XAttribute(officeRel + "id", "rId1"))))));
        WriteXmlEntry(archive, "xl/_rels/workbook.xml.rels", new XDocument(
            new XElement(rel + "Relationships",
                new XElement(rel + "Relationship",
                    new XAttribute("Id", "rId1"),
                    new XAttribute("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"),
                    new XAttribute("Target", "worksheets/sheet1.xml")))));

        var sheetData = new XElement(sheet + "sheetData",
            MakeInlineStringRow(1, ("A1", "Quarter"), ("B1", "Revenue")),
            MakeChartWorkbookRow(2, "Q1", "12"),
            MakeChartWorkbookRow(3, "Q2", "18"),
            MakeChartWorkbookRow(4, "Q3", "15"));
        WriteXmlEntry(archive, "xl/worksheets/sheet1.xml", new XDocument(
            new XElement(sheet + "worksheet", sheetData)));
    }
    return output.ToArray();
}

static XElement MakeInlineStringRow(int rowNumber, params (string address, string text)[] cells)
{
    XNamespace sheet = "http://schemas.openxmlformats.org/spreadsheetml/2006/main";
    return new XElement(sheet + "row", new XAttribute("r", rowNumber),
        cells.Select(cell => new XElement(sheet + "c",
            new XAttribute("r", cell.address),
            new XAttribute("t", "inlineStr"),
            new XElement(sheet + "is", new XElement(sheet + "t", cell.text)))));
}

static XElement MakeChartWorkbookRow(int rowNumber, string category, string value)
{
    XNamespace sheet = "http://schemas.openxmlformats.org/spreadsheetml/2006/main";
    return new XElement(sheet + "row", new XAttribute("r", rowNumber),
        new XElement(sheet + "c", new XAttribute("r", $"A{rowNumber}"), new XAttribute("t", "inlineStr"),
            new XElement(sheet + "is", new XElement(sheet + "t", category))),
        new XElement(sheet + "c", new XAttribute("r", $"B{rowNumber}"), new XElement(sheet + "v", value)));
}

static void WriteXmlEntry(ZipArchive archive, string name, XDocument document)
{
    var entry = archive.CreateEntry(name, CompressionLevel.Optimal);
    using var stream = entry.Open();
    document.Save(stream, SaveOptions.DisableFormatting);
}

static void UpdateChartValue(string path, string name, int pointIndex, string updatedValue)
{
    using var document = PresentationDocument.Open(path, isEditable: true);
    var slidePart = document.PresentationPart?.SlideParts.SingleOrDefault()
        ?? throw new InvalidDataException("Expected exactly one slide for the chart update case.");
    var slide = slidePart.Slide ?? throw new InvalidDataException("Slide root is missing from the chart update part.");
    var frame = slide.CommonSlideData?.ShapeTree?.Elements<P.GraphicFrame>()
        .SingleOrDefault(candidate => candidate.NonVisualGraphicFrameProperties?.NonVisualDrawingProperties?.Name?.Value == name)
        ?? throw new InvalidDataException($"Chart graphic frame {name} was not found.");
    var chartReference = frame.Graphic?.GraphicData?.GetFirstChild<C.ChartReference>()
        ?? throw new InvalidDataException($"Chart graphic frame {name} has no chart reference.");
    var chartPart = slidePart.GetPartById(chartReference.Id!.Value!) as ChartPart
        ?? throw new InvalidDataException($"Chart reference for {name} does not resolve to a ChartPart.");
    XNamespace chartNamespace = "http://schemas.openxmlformats.org/drawingml/2006/chart";
    var chartDocument = XDocument.Parse(chartPart.ChartSpace?.OuterXml
        ?? throw new InvalidDataException("ChartSpace is missing."));
    var value = chartDocument.Descendants(chartNamespace + "numCache")
        .Single()
        .Elements(chartNamespace + "pt")
        .Single(point => (string?)point.Attribute("idx") == pointIndex.ToString())
        .Element(chartNamespace + "v")
        ?? throw new InvalidDataException($"Chart value point {pointIndex} was not found.");
    value.Value = updatedValue;
    chartPart.ChartSpace = new C.ChartSpace(chartDocument.ToString(SaveOptions.DisableFormatting));
    chartPart.ChartSpace.Save();

    var embeddedWorkbook = chartPart.EmbeddedPackagePart
        ?? throw new InvalidDataException("Embedded chart workbook part is missing.");
    byte[] originalWorkbookBytes;
    using (var originalWorkbookStream = embeddedWorkbook.GetStream(FileMode.Open, FileAccess.Read))
    using (var originalWorkbook = new MemoryStream())
    {
        originalWorkbookStream.CopyTo(originalWorkbook);
        originalWorkbookBytes = originalWorkbook.ToArray();
    }
    var updatedWorkbookBytes = UpdateEmbeddedWorkbookCell(originalWorkbookBytes, "B3", updatedValue);
    using var updatedWorkbookStream = new MemoryStream(updatedWorkbookBytes, writable: false);
    embeddedWorkbook.FeedData(updatedWorkbookStream);
    slide.Save();
}

static byte[] UpdateEmbeddedWorkbookCell(byte[] workbookBytes, string cellAddress, string value)
{
    XNamespace sheet = "http://schemas.openxmlformats.org/spreadsheetml/2006/main";
    using var workbookStream = new MemoryStream(workbookBytes);
    using (var archive = new ZipArchive(workbookStream, ZipArchiveMode.Update, leaveOpen: true))
    {
        var entry = archive.GetEntry("xl/worksheets/sheet1.xml")
            ?? throw new InvalidDataException("Embedded chart workbook worksheet is missing.");
        XDocument worksheet;
        using (var input = entry.Open())
        {
            worksheet = XDocument.Load(input);
        }
        var cell = worksheet.Descendants(sheet + "c")
            .SingleOrDefault(candidate => (string?)candidate.Attribute("r") == cellAddress)
            ?? throw new InvalidDataException($"Embedded chart workbook cell {cellAddress} is missing.");
        cell.Attribute("t")?.Remove();
        cell.Elements(sheet + "v").Remove();
        cell.Add(new XElement(sheet + "v", value));
        entry.Delete();
        WriteXmlEntry(archive, "xl/worksheets/sheet1.xml", worksheet);
    }
    return workbookStream.ToArray();
}

static ChartSnapshot ReadChartSnapshot(string path, string name)
{
    using var document = PresentationDocument.Open(path, isEditable: false);
    var slidePart = document.PresentationPart?.SlideParts.SingleOrDefault()
        ?? throw new InvalidDataException("Expected exactly one slide for the chart snapshot case.");
    var slide = slidePart.Slide ?? throw new InvalidDataException("Slide root is missing from the chart snapshot part.");
    var frame = slide.CommonSlideData?.ShapeTree?.Elements<P.GraphicFrame>()
        .SingleOrDefault(candidate => candidate.NonVisualGraphicFrameProperties?.NonVisualDrawingProperties?.Name?.Value == name)
        ?? throw new InvalidDataException($"Chart graphic frame {name} was not found.");
    var drawingProperties = frame.NonVisualGraphicFrameProperties?.NonVisualDrawingProperties
        ?? throw new InvalidDataException($"Chart graphic frame {name} has no identity properties.");
    var transform = frame.Transform ?? throw new InvalidDataException($"Chart graphic frame {name} has no bounds.");
    var chartReference = frame.Graphic?.GraphicData?.GetFirstChild<C.ChartReference>()
        ?? throw new InvalidDataException($"Chart graphic frame {name} has no chart reference.");
    var chartPart = slidePart.GetPartById(chartReference.Id!.Value!) as ChartPart
        ?? throw new InvalidDataException($"Chart reference for {name} does not resolve to a ChartPart.");
    var chartSpace = chartPart.ChartSpace ?? throw new InvalidDataException("ChartSpace is missing.");
    var chartDocument = XDocument.Parse(chartSpace.OuterXml);
    XNamespace chart = "http://schemas.openxmlformats.org/drawingml/2006/chart";
    XNamespace drawing = "http://schemas.openxmlformats.org/drawingml/2006/main";
    XNamespace officeRel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships";
    var chartElement = chartDocument.Root?.Element(chart + "chart") ?? throw new InvalidDataException("Chart element is missing.");
    var plotArea = chartElement.Element(chart + "plotArea") ?? throw new InvalidDataException("Chart plot area is missing.");
    var series = plotArea.Descendants(chart + "ser").SingleOrDefault() ?? throw new InvalidDataException("Expected exactly one chart series.");
    var categories = series.Element(chart + "cat")?.Descendants(chart + "strCache").Elements(chart + "pt")
        .Select(point => point.Element(chart + "v")?.Value ?? string.Empty).ToArray() ?? [];
    var values = series.Element(chart + "val")?.Descendants(chart + "numCache").Elements(chart + "pt")
        .Select(point => point.Element(chart + "v")?.Value ?? string.Empty).ToArray() ?? [];
    var embeddedWorkbook = chartPart.EmbeddedPackagePart
        ?? throw new InvalidDataException("Embedded chart workbook part is missing.");
    var externalRelationshipId = chartDocument.Root?.Element(chart + "externalData")?.Attribute(officeRel + "id")?.Value;
    var chartType = plotArea.Elements().FirstOrDefault(element => element.Name != chart + "layout")?.Name.LocalName;
    var axisIds = plotArea.Elements()
        .Where(element => element.Name == chart + "catAx" || element.Name == chart + "valAx")
        .Select(axis => axis.Element(chart + "axId")?.Attribute("val")?.Value ?? string.Empty)
        .ToArray();
    using var embeddedStream = embeddedWorkbook.GetStream(FileMode.Open, FileAccess.Read);
    using var embeddedBytes = new MemoryStream();
    embeddedStream.CopyTo(embeddedBytes);
    var workbookData = embeddedBytes.ToArray();

    return new ChartSnapshot(
        drawingProperties.Id?.Value,
        drawingProperties.Name?.Value,
        transform.Offset?.X?.Value,
        transform.Offset?.Y?.Value,
        transform.Extents?.Cx?.Value,
        transform.Extents?.Cy?.Value,
        string.Concat(chartElement.Element(chart + "title")?.Descendants(drawing + "t").Select(text => text.Value) ?? []),
        chartType,
        series.Element(chart + "tx")?.Descendants(chart + "strCache").Elements(chart + "pt").FirstOrDefault()?.Element(chart + "v")?.Value,
        categories,
        values,
        series.Element(chart + "tx")?.Descendants(chart + "strRef").Elements(chart + "f").FirstOrDefault()?.Value,
        series.Element(chart + "cat")?.Descendants(chart + "strRef").Elements(chart + "f").FirstOrDefault()?.Value,
        series.Element(chart + "val")?.Descendants(chart + "numRef").Elements(chart + "f").FirstOrDefault()?.Value,
        axisIds,
        chartElement.Element(chart + "legend") is not null,
        chartElement.Descendants(chart + "showVal").Any(element => (string?)element.Attribute("val") == "1"),
        externalRelationshipId,
        chartPart.GetIdOfPart(embeddedWorkbook),
        ReadEmbeddedWorkbookCell(workbookData, "B3"),
        Sha256Bytes(workbookData));
}

static string ReadEmbeddedWorkbookCell(byte[] workbookBytes, string cellAddress)
{
    XNamespace sheet = "http://schemas.openxmlformats.org/spreadsheetml/2006/main";
    using var input = new MemoryStream(workbookBytes, writable: false);
    using var archive = new ZipArchive(input, ZipArchiveMode.Read);
    var entry = archive.GetEntry("xl/worksheets/sheet1.xml")
        ?? throw new InvalidDataException("Embedded chart workbook worksheet is missing.");
    using var stream = entry.Open();
    var worksheet = XDocument.Load(stream);
    return worksheet.Descendants(sheet + "c")
        .SingleOrDefault(cell => (string?)cell.Attribute("r") == cellAddress)?
        .Element(sheet + "v")?.Value
        ?? throw new InvalidDataException($"Embedded chart workbook cell {cellAddress} is missing.");
}

static ValidationResult ValidateEmbeddedWorkbook(string presentationPath, string chartName)
{
    using var presentation = PresentationDocument.Open(presentationPath, isEditable: false);
    var slidePart = presentation.PresentationPart?.SlideParts.SingleOrDefault()
        ?? throw new InvalidDataException("Expected exactly one slide to validate the embedded chart workbook.");
    var slide = slidePart.Slide ?? throw new InvalidDataException("Slide root is missing from embedded workbook validation.");
    var frame = slide.CommonSlideData?.ShapeTree?.Elements<P.GraphicFrame>()
        .SingleOrDefault(candidate => candidate.NonVisualGraphicFrameProperties?.NonVisualDrawingProperties?.Name?.Value == chartName)
        ?? throw new InvalidDataException($"Chart graphic frame {chartName} was not found.");
    var chartReference = frame.Graphic?.GraphicData?.GetFirstChild<C.ChartReference>()
        ?? throw new InvalidDataException("Chart reference is missing.");
    var chartPart = slidePart.GetPartById(chartReference.Id!.Value!) as ChartPart
        ?? throw new InvalidDataException("Chart reference does not resolve to a ChartPart.");
    var embeddedPart = chartPart.EmbeddedPackagePart ?? throw new InvalidDataException("Embedded chart workbook part is missing.");
    using var input = embeddedPart.GetStream(FileMode.Open, FileAccess.Read);
    using var memory = new MemoryStream();
    input.CopyTo(memory);
    using var workbook = SpreadsheetDocument.Open(new MemoryStream(memory.ToArray(), writable: false), isEditable: false);
    var errors = new OpenXmlValidator(FileFormatVersions.Office2019)
        .Validate(workbook)
        .Take(20)
        .Select(error => $"{error.ErrorType}: {error.Description} ({error.Path?.XPath})")
        .ToArray();
    return new ValidationResult(errors.Length, errors);
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

internal sealed record ShapeSnapshot(
    uint? ShapeId,
    string? Name,
    long? X,
    long? Y,
    long? Cx,
    long? Cy,
    string? PresetGeometry,
    string? FillColor,
    string? OutlineColor,
    string Text);

internal sealed record ShapeMutationResult(
    string Status,
    string TestScope,
    string InputFile,
    string OutputFile,
    string OutputSha256,
    string ShapeName,
    ShapeSnapshot Before,
    ShapeSnapshot After,
    bool GeometryPreserved,
    bool TextUpdated,
    int ValidatorErrorCount,
    string[] ValidatorErrors);

internal sealed record ImageSnapshot(
    uint? ShapeId,
    string? Name,
    string? AltText,
    string RelationshipId,
    string ContentType,
    string ImageSha256,
    long? X,
    long? Y,
    long? Cx,
    long? Cy);

internal sealed record ImageRoundTripResult(
    string Status,
    string TestScope,
    string InputFile,
    string OutputFile,
    string OutputSha256,
    string ImageName,
    string AltText,
    string OriginalImageSha256,
    string ReplacementImageSha256,
    ImageSnapshot Before,
    ImageSnapshot After,
    bool BoundsPreserved,
    bool IdentityPreserved,
    bool ImageReplaced,
    int ValidatorErrorCount,
    string[] ValidatorErrors);

internal sealed record TableSnapshot(
    uint? ShapeId,
    string? Name,
    long? X,
    long? Y,
    long? Cx,
    long? Cy,
    int RowCount,
    int ColumnCount,
    string[][] Cells);

internal sealed record TableRoundTripResult(
    string Status,
    string TestScope,
    string InputFile,
    string OutputFile,
    string OutputSha256,
    string TableName,
    TableSnapshot Before,
    TableSnapshot After,
    bool IdentityAndGeometryPreserved,
    bool TableDimensionsPreserved,
    bool TextUpdated,
    int ValidatorErrorCount,
    string[] ValidatorErrors);

internal sealed record ChartSnapshot(
    uint? ShapeId,
    string? Name,
    long? X,
    long? Y,
    long? Cx,
    long? Cy,
    string Title,
    string? ChartType,
    string? SeriesName,
    string[] Categories,
    string[] Values,
    string? SeriesFormula,
    string? CategoryFormula,
    string? ValuesFormula,
    string[] AxisIds,
    bool HasLegend,
    bool HasValueLabels,
    string? EmbeddedRelationshipId,
    string EmbeddedWorkbookRelationshipId,
    string EmbeddedWorkbookValue,
    string EmbeddedWorkbookSha256);

internal sealed record ChartRoundTripResult(
    string Status,
    string TestScope,
    string InputFile,
    string OutputFile,
    string OutputSha256,
    string ChartName,
    ChartSnapshot Before,
    ChartSnapshot After,
    bool IdentityAndGeometryPreserved,
    bool ChartDefinitionPreserved,
    bool DataUpdated,
    int ValidatorErrorCount,
    string[] ValidatorErrors,
    int EmbeddedWorkbookValidatorErrorCount,
    string[] EmbeddedWorkbookValidatorErrors);

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
