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
var semanticPreservation = CompareMasterLayoutThemePartsSemantically(fixturePath, outputPath);
var validation = Validate(outputPath);
var existingShapeMutation = RunExistingShapeMutation(fixturePath, artifacts);
var imageRoundTrip = RunImageRoundTrip(fixturePath, artifacts);
var tableRoundTrip = RunTableRoundTrip(fixturePath, artifacts);

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
        unknown_part_preservation = unknownPartTest.Status,
        chart_notes_comments_transitions_animations_media = "untested",
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
        "Chart/notes/comments/transition/animation/media authoring and mutation were not exercised."
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
