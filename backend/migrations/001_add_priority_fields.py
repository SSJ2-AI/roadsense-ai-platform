"""
Migration: Add priority and area analysis fields to existing detections.

This migration follows the Expand-Migrate-Contract pattern:
1. Expand: Add new fields with default values (non-breaking)
2. Migrate: Backfill data for existing records
3. Contract: Remove old fields (if any) - not needed for this migration

Usage:
    python migrations/001_add_priority_fields.py --project PROJECT_ID

Notes:
- This script is idempotent - safe to run multiple times
- Updates detections in batches to avoid memory issues
- Adds: severity, priority_score, area, street_name, status, repair_urgency, cluster_id, road_type
"""

import argparse
from datetime import datetime, timezone
from google.cloud import firestore
import sys


def calculate_severity(num_detections: int, max_confidence: float) -> str:
    """Calculate severity based on detection count and confidence."""
    if num_detections >= 3 or max_confidence > 0.9:
        return "high"
    elif num_detections == 2 or (0.7 <= max_confidence <= 0.9):
        return "medium"
    else:
        return "low"


def calculate_priority_score(severity: str, num_detections: int) -> int:
    """Calculate priority score."""
    severity_scores = {"low": 25, "medium": 50, "high": 75}
    score = severity_scores.get(severity, 25)
    score += min(num_detections * 5, 20)
    return min(max(score, 0), 100)


def migrate_detection(doc_ref, doc_data, dry_run=False):
    """Migrate a single detection record."""
    # Check if already migrated
    if doc_data.get("severity") is not None:
        return False, "Already migrated"
    
    # Extract detection data
    detection = doc_data.get("detection", {})
    num_detections = detection.get("numDetections", 0)
    bounding_boxes = detection.get("boundingBoxes", [])
    
    # Calculate max confidence
    max_confidence = 0.0
    if bounding_boxes:
        max_confidence = max([bb.get("confidence", 0.0) for bb in bounding_boxes])
    
    # Calculate severity and priority
    severity = calculate_severity(num_detections, max_confidence)
    priority_score = calculate_priority_score(severity, num_detections)
    
    # Determine repair urgency
    repair_urgency = "routine"
    if severity == "high":
        repair_urgency = "emergency"
    elif severity == "medium":
        repair_urgency = "urgent"
    
    # Update document with new fields
    updates = {
        "severity": severity,
        "priority_score": priority_score,
        "area": None,  # Will be populated by reverse geocoding
        "street_name": None,  # Will be populated by reverse geocoding
        "status": "reported",  # Default status for existing records
        "repair_urgency": repair_urgency,
        "cluster_id": None,  # Will be populated by clustering algorithm
        "road_type": "residential",  # Default value
        "migratedAt": datetime.now(timezone.utc),
    }
    
    # Skip actual update in dry-run mode
    if not dry_run:
        doc_ref.update(updates)
    
    return True, "Migrated successfully" if not dry_run else "Would migrate (dry-run)"


def run_migration(project_id: str, collection_name: str = "detections", batch_size: int = 100, dry_run: bool = False):
    """Run the migration on all detection documents."""
    print(f"Starting migration for project: {project_id}")
    print(f"Collection: {collection_name}")
    print(f"Batch size: {batch_size}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("-" * 60)
    
    # Initialize Firestore client
    db = firestore.Client(project=project_id)
    
    # Fetch all documents
    collection_ref = db.collection(collection_name)
    docs = collection_ref.stream()
    
    migrated_count = 0
    skipped_count = 0
    error_count = 0
    
    for doc in docs:
        try:
            doc_data = doc.to_dict()
            success, message = migrate_detection(doc.reference, doc_data, dry_run=dry_run)
            
            if success:
                migrated_count += 1
                print(f"✓ {'Would migrate' if dry_run else 'Migrated'}: {doc.id}")
            else:
                skipped_count += 1
                print(f"⊘ Skipped: {doc.id} - {message}")
        except Exception as e:
            error_count += 1
            print(f"✗ Error: {doc.id} - {str(e)}")
    
    print("-" * 60)
    print(f"Migration {'preview' if dry_run else 'complete'}!")
    print(f"  {'Would migrate' if dry_run else 'Migrated'}: {migrated_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {migrated_count + skipped_count + error_count}")
    
    return migrated_count, skipped_count, error_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate detections to add priority fields")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    parser.add_argument("--collection", default="detections", help="Firestore collection name")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode (no actual updates)")
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("⚠️  DRY RUN MODE - No changes will be made")
        print()
    
    try:
        migrated, skipped, errors = run_migration(
            args.project,
            args.collection,
            args.batch_size,
            dry_run=args.dry_run
        )
        
        if errors > 0:
            sys.exit(1)
        else:
            sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)
