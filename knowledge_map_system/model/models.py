# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class TAlgorithm(models.Model):
    algorithm_name = models.CharField(max_length=20, blank=True, null=True)
    algorithm_mask = models.CharField(max_length=20, blank=True, null=True)
    algorithm_type = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 't_algorithm'


class TAttrbuteAlias(models.Model):
    attribute_id = models.IntegerField(blank=True, null=True)
    attribute_alias = models.CharField(max_length=20, blank=True, null=True)
    create_id = models.IntegerField(blank=True, null=True)
    create_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 't_attrbute_alias'


class TAttribute(models.Model):
    attribute_name = models.CharField(max_length=20, blank=True, null=True)
    data_type_id = models.IntegerField(blank=True, null=True)
    is_single_value = models.IntegerField(blank=True, null=True)
    attribute_description = models.TextField(blank=True, null=True)
    category_id = models.IntegerField(blank=True, null=True)
    create_time = models.DateTimeField(blank=True, null=True)
    algorithm_id = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 't_attribute'


class TAttributeMapLog(models.Model):
    attribute_name = models.CharField(max_length=20, blank=True, null=True)
    is_map = models.IntegerField(blank=True, null=True)
    entity_id = models.CharField(max_length=30, blank=True, null=True)
    map_attribute_id = models.IntegerField(blank=True, null=True)
    create_id = models.IntegerField(blank=True, null=True)
    map_rule_id = models.IntegerField(blank=True, null=True)
    repo_id = models.IntegerField(blank=True, null=True)
    category_id = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 't_attribute_map_log'


class TCategory(models.Model):
    category_name = models.CharField(max_length=20, blank=True, null=True)
    father_category_id = models.CharField(max_length=20, blank=True, null=True)
    is_temporary = models.IntegerField(blank=True, null=True)
    category_description = models.TextField(blank=True, null=True)
    repo_id = models.IntegerField(blank=True, null=True)
    create_id = models.IntegerField(blank=True, null=True)
    create_time = models.DateTimeField(blank=True, null=True)
    category_level = models.IntegerField(blank=True, null=True)
    category_type = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 't_category'


class TCleaningLog(models.Model):
    entity_id = models.CharField(max_length=30, blank=True, null=True)
    user_id = models.IntegerField(blank=True, null=True)
    cleaning_rule_id = models.IntegerField(blank=True, null=True)
    cleaning_content = models.TextField(blank=True, null=True)
    cleaning_result = models.TextField(blank=True, null=True)
    category_id = models.IntegerField(blank=True, null=True)
    repo_id = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 't_cleaning_log'


class TCleaningRule(models.Model):
    attribute_id = models.IntegerField(blank=True, null=True)
    is_cleaning = models.IntegerField(blank=True, null=True)
    cleaning_rule = models.CharField(max_length=20, blank=True, null=True)
    create_time = models.DateTimeField(blank=True, null=True)
    create_id = models.IntegerField(blank=True, null=True)
    category_id = models.IntegerField(blank=True, null=True)
    is_custom = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 't_cleaning_rule'


class TDataAcquisitionLog(models.Model):
    create_time = models.DateTimeField(blank=True, null=True)
    data_source_name = models.TextField(blank=True, null=True)
    data_access = models.CharField(max_length=20, blank=True, null=True)
    data_path = models.TextField(blank=True, null=True)
    repo_id = models.IntegerField(blank=True, null=True)
    create_id = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 't_data_acquisition_log'


class TDataType(models.Model):
    datatype_name = models.CharField(max_length=20, blank=True, null=True)
    category_id = models.IntegerField(blank=True, null=True)
    repo_id = models.IntegerField(blank=True, null=True)
    create_id = models.IntegerField(blank=True, null=True)
    create_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 't_data_type'


class TEntityExtractionLog(models.Model):
    data_acquisition_id = models.IntegerField(blank=True, null=True)
    is_extract = models.IntegerField(blank=True, null=True)
    entity_number = models.IntegerField(blank=True, null=True)
    extract_time = models.DateTimeField(blank=True, null=True)
    create_id = models.IntegerField(blank=True, null=True)
    repo_id = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 't_entity_extraction_log'


class TMappingRule(models.Model):
    attribute_name = models.CharField(max_length=20, blank=True, null=True)
    coverage_rate = models.FloatField(blank=True, null=True)
    map_attribute_id = models.IntegerField(blank=True, null=True)
    create_time = models.DateTimeField(blank=True, null=True)
    category_id = models.IntegerField(blank=True, null=True)
    create_id = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 't_mapping_rule'


class TNormalizedLog(models.Model):
    merge_entity_id = models.CharField(max_length=30, blank=True, null=True)
    original_entity_id1 = models.TextField(blank=True, null=True)
    original_entity_id2 = models.TextField(blank=True, null=True)
    normalized_rule_id = models.IntegerField(blank=True, null=True)
    create_id = models.IntegerField(blank=True, null=True)
    repo_id = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 't_normalized_log'


class TNormalizedRule(models.Model):
    category_id = models.IntegerField(blank=True, null=True)
    rule_number = models.IntegerField(blank=True, null=True)
    update_time = models.DateTimeField(blank=True, null=True)
    overall_threshold = models.FloatField(blank=True, null=True)
    repo_id = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 't_normalized_rule'


class TNormalizedRuleDetail(models.Model):
    normalized_rule_id = models.IntegerField(blank=True, null=True)
    attribute_id = models.IntegerField(blank=True, null=True)
    similarity_threshold = models.FloatField(blank=True, null=True)
    update_time = models.DateTimeField(blank=True, null=True)
    create_id = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 't_normalized_rule_detail'


class TRepository(models.Model):
    repo_name = models.CharField(max_length=20, blank=True, null=True)
    repo_description = models.TextField(blank=True, null=True)
    create_id = models.IntegerField(blank=True, null=True)
    create_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 't_repository'


class TSpiderDatatype(models.Model):
    data_type_name = models.CharField(max_length=20, blank=True, null=True)
    data_type_mask = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 't_spider_datatype'


class TSpiderDatawebsite(models.Model):
    website_name = models.CharField(max_length=20, blank=True, null=True)
    website_mask = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 't_spider_datawebsite'


class TSpiderProject(models.Model):
    data_website_id = models.IntegerField(blank=True, null=True)
    data_type_id = models.IntegerField(blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    create_id = models.IntegerField(blank=True, null=True)
    repo_id = models.IntegerField(blank=True, null=True)
    create_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 't_spider_project'


class TUser(models.Model):
    user_account = models.CharField(max_length=20, blank=True, null=True)
    user_password = models.CharField(max_length=20, blank=True, null=True)
    user_name = models.CharField(max_length=20, blank=True, null=True)
    create_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 't_user'


class TEventRule(models.Model):
    event_subject_id = models.IntegerField(blank=True, null=True)
    event_object_id = models.IntegerField(blank=True, null=True)
    category_id = models.IntegerField(blank=True, null=True)
    repo_id = models.IntegerField(blank=True, null=True)
    algorithm_id = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 't_event_rule'


class TTriggerWord(models.Model):
    trigger_word = models.CharField(max_length=20, blank=True, null=True)
    event_rule_id = models.IntegerField(blank=True, null=True)
    repo_id = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 't_trigger_word'
