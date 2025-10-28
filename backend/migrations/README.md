# Database Migrations

This directory contains database migration scripts for the RoadSense backend.

## Migration Strategy

We follow the **Expand-Migrate-Contract** pattern for zero-downtime deployments:

1. **Expand**: Add new fields/columns with default values (non-breaking change)
2. **Migrate**: Backfill data for existing records
3. **Contract**: Remove old fields/columns (only if necessary)

## Running Migrations

### Prerequisites

- Python 3.9+
- Google Cloud credentials configured
- Access to the Firestore database

### Execute a Migration

```bash
# Set up environment
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# Run migration
python migrations/001_add_priority_fields.py --project YOUR_PROJECT_ID

# Dry run (no actual changes)
python migrations/001_add_priority_fields.py --project YOUR_PROJECT_ID --dry-run
```

## Available Migrations

### 001_add_priority_fields.py

**Date**: 2025-10-28  
**Description**: Adds priority and area analysis fields to existing detection records.

**Fields Added**:
- `severity`: str (low/medium/high)
- `priority_score`: int (0-100)
- `area`: str (neighborhood name, initially null)
- `street_name`: str (initially null)
- `status`: str (default: "reported")
- `repair_urgency`: str (routine/urgent/emergency)
- `cluster_id`: str (initially null)
- `road_type`: str (default: "residential")

**Breaking Changes**: None (all fields are optional/have defaults)

**Rollback**: Not required - new fields are optional and don't affect existing functionality.

## Best Practices

### Before Running Migrations

1. **Backup your data**: Create a Firestore export
   ```bash
   gcloud firestore export gs://YOUR_BUCKET/backups/$(date +%Y%m%d)
   ```

2. **Test in staging first**: Always run migrations in staging before production

3. **Review the migration code**: Ensure you understand what changes will be made

4. **Check feature flags**: Ensure related features are disabled during migration

### During Migration

1. **Monitor progress**: Watch the console output for errors
2. **Check Firestore metrics**: Monitor read/write operations in GCP Console
3. **Be patient**: Large collections may take time to migrate

### After Migration

1. **Verify data**: Check a sample of migrated records
2. **Enable features**: Turn on related feature flags in config
3. **Monitor application**: Watch for errors or unexpected behavior
4. **Document**: Update this README with migration results

## Rollback Procedures

If a migration causes issues:

1. **Disable feature flags** immediately in `backend/app/config.py`:
   ```python
   ENABLE_PRIORITY_SCORING = False
   ENABLE_CLUSTERING = False
   ENABLE_ANALYTICS = False
   ```

2. **Restore from backup** (if necessary):
   ```bash
   gcloud firestore import gs://YOUR_BUCKET/backups/BACKUP_DATE
   ```

3. **Investigate and fix**: Review errors, fix migration script, test in staging

## Migration Checklist

- [ ] Backup database
- [ ] Test in staging environment
- [ ] Review migration code
- [ ] Disable related feature flags
- [ ] Run migration with --dry-run
- [ ] Run actual migration
- [ ] Verify migrated data
- [ ] Enable feature flags
- [ ] Monitor application
- [ ] Document results

## Support

For issues or questions about migrations:
- Check Cloud Run logs: `gcloud run logs read roadsense-backend`
- Check Firestore in GCP Console
- Review migration script output
- Contact the development team
