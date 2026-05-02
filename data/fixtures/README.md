# Fixture Data Index

This directory contains sample source data fixtures for testing Agora OSS contracts and integrations.

## Drupal.org Fixtures

### sources/drupalorg/

- **actors_sample.json** (3 records)
  - Sample Drupal.org users for actor entity testing
  - Includes roles, relationships (maintains, contributes_to)

- **projects_sample.json** (3 records)
  - Sample Drupal.org projects (modules) for project entity testing
  - Includes relationships (part_of, depends_on)

- **issues_sample.json** (3 records)
  - Sample Drupal.org issues for issue entity testing
  - Mix of open and closed issues
  - Includes relationships (reported, assigned_to)

### canonical/drupalorg/

- **actors_sample_canonical.json**
  - Expected canonical output for actors_sample.json
  - Used for dry-run mapping validation

- **projects_sample_canonical.json**
  - Expected canonical output for projects_sample.json

## WordPress.org Fixtures

### sources/wordpressorg/

- **authors_sample.json** (3 records)
  - Sample WordPress.org plugin authors for actor entity testing

- **plugins_sample.json** (3 records)
  - Sample WordPress.org plugins for project entity testing

## Testing Fixtures

Run mapping dry-runs against fixtures:

```bash
# Test Drupal.org mapping
python -m agora.mapping dryrun \
  --source-family drupalorg \
  --mapping configs/mappings/drupalorg/default.mapping.yaml \
  --fixtures data/fixtures/sources/drupalorg/

# Test WordPress.org mapping
python -m agora.mapping dryrun \
  --source-family wordpressorg \
  --mapping configs/mappings/wordpressorg/default.mapping.yaml \
  --fixtures data/fixtures/sources/wordpressorg/
```

## Contributing Fixtures

When adding new fixtures:

1. Add real or realistic sample data to `sources/{source_family}/`
2. Generate corresponding expected canonical output to `canonical/{source_family}/`
3. Update this index with record count and entity type descriptions
4. Ensure all required fields are present
5. Use realistic but non-sensitive data (no real names/emails from actual people)

## Fixture Evolution

Fixtures are versioned with the mapping packs. When mapping rules change, fixtures may need updating.

See canonical-entities-v1.md and mapping-rules-v1.md for data format details.
