from ingestion.internal.classifier import InternalDocumentClassifier


def test_classifier_identifies_runbook():
    classifier = InternalDocumentClassifier()

    result = classifier.classify(
        "knowledge/runbooks/oracle_performance.md"
    )

    assert result == "runbook"


def test_classifier_identifies_sop():
    classifier = InternalDocumentClassifier()

    result = classifier.classify(
        "knowledge/sop/database_backup.md"
    )

    assert result == "sop"


def test_classifier_identifies_rca():
    classifier = InternalDocumentClassifier()

    result = classifier.classify(
        "knowledge/rca/database_incident.md"
    )

    assert result == "rca"


def test_classifier_identifies_architecture():
    classifier = InternalDocumentClassifier()

    result = classifier.classify(
        "knowledge/architecture/database_platform.md"
    )

    assert result == "architecture"


def test_classifier_defaults_to_internal():
    classifier = InternalDocumentClassifier()

    result = classifier.classify(
        "knowledge/general/database_notes.md"
    )

    assert result == "internal"


def test_classifier_does_not_match_partial_directory_name():
    classifier = InternalDocumentClassifier()

    result = classifier.classify(
        "knowledge/runbooks_backup/database_notes.md"
    )

    assert result == "internal"
