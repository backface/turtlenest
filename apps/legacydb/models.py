# This is an auto-generated Django model module.
#
# Cleaned and Foreign Keys removed (set to InegerFields)

from django.db import models


class LegacyDbModel(models.Model):
    class Meta:
        abstract = True
        _db = "legacydb"


class ClassroomMembers(LegacyDbModel):
    classroom_id = models.IntegerField()
    is_teaching = models.BooleanField()
    # username = models.ForeignKey('Users', models.DO_NOTHING, db_column='username', blank=True, null=True)
    username = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "classroom_members"
        unique_together = (("classroom_id", "username"),)
        verbose_name_plural = "classroom_members"


class ClassroomProjects(LegacyDbModel):
    classroom_id = models.IntegerField()
    project_id = models.IntegerField()
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    is_starter = models.BooleanField()
    unit = models.IntegerField()

    class Meta:
        managed = False
        db_table = "classroom_projects"
        verbose_name_plural = "classroom_projects"


class ClassroomUnits(LegacyDbModel):
    classroom_id = models.IntegerField()
    title = models.TextField()
    number = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    image = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "classroom_units"
        verbose_name_plural = "classroom_units"


class Classrooms(LegacyDbModel):
    title = models.TextField()
    description = models.TextField(blank=True, null=True)
    image = models.TextField(blank=True, null=True)
    # host = models.ForeignKey('Users', models.DO_NOTHING, db_column='host', blank=True, null=True)
    host = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    current_unit = models.IntegerField()
    introduction = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "classrooms"
        verbose_name_plural = "classrooms"


class Comments(LegacyDbModel):
    # projectname = models.ForeignKey('Projects', models.DO_NOTHING, db_column='projectname', to_field='projectname', blank=True, null=True)
    projectname = models.TextField(blank=True, null=True)
    projectowner = models.TextField(blank=True, null=True)
    # author = models.ForeignKey('Users', models.DO_NOTHING, db_column='author', blank=True, null=True)
    author = models.TextField(blank=True, null=True)
    contents = models.TextField(blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "comments"
        verbose_name_plural = "comments"


class LapisMigrations(LegacyDbModel):
    name = models.CharField(primary_key=True, max_length=255)

    class Meta:
        managed = False
        db_table = "lapis_migrations"
        verbose_name_plural = "lapis_migrations"


class Likes(LegacyDbModel):
    # liker = models.ForeignKey('Users', models.DO_NOTHING, db_column='liker', blank=True, null=True)
    liker = models.TextField(blank=True, null=True)
    projectname = models.TextField(blank=True, null=True)
    projectowner = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "likes"
        verbose_name_plural = "likes"


class Pages(LegacyDbModel):
    id = models.AutoField(primary_key=True)
    slug = models.TextField(unique=True)
    title = models.TextField()
    content = models.TextField(blank=True, null=True)
    last_edit_by = models.TextField(db_column="last_edit_by", blank=True, null=True)
    last_edit_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "pages"
        verbose_name_plural = "pages"


class Projects(LegacyDbModel):
    projectname = models.TextField()
    ispublic = models.BooleanField(blank=True, null=True)
    contents = models.TextField(blank=True, null=True)
    thumbnail = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    updated = models.DateTimeField(blank=True, null=True)
    # username = models.OneToOneField('Users', models.DO_NOTHING, db_column='username')  # The composite primary key (username, projectname) found, that is not supported. The first column is selected.
    username = models.TextField(blank=True, null=True)
    id = models.AutoField(primary_key=True)
    shared = models.DateTimeField(blank=True, null=True)
    views = models.IntegerField(blank=True, null=True)
    imageisfeatured = models.BooleanField(blank=True, null=True)
    categories = models.TextField(blank=True, null=True)
    created = models.DateTimeField(blank=True, null=True)
    origcreator = models.TextField(blank=True, null=True)
    origname = models.TextField(blank=True, null=True)
    remixhistory = models.TextField(blank=True, null=True)
    tags = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "projects"
        unique_together = (("username", "projectname"),)
        verbose_name_plural = "projects"


class Users(LegacyDbModel):
    username = models.TextField(unique=True)
    email = models.TextField(unique=True, blank=True, null=True)
    password = models.TextField(blank=True, null=True)
    joined = models.DateTimeField(blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    location = models.TextField(blank=True, null=True)
    isadmin = models.BooleanField(blank=True, null=True)
    reset_code = models.TextField(blank=True, null=True)
    notify_comment = models.BooleanField(blank=True, null=True)
    notify_like = models.BooleanField(blank=True, null=True)
    confirmed = models.BooleanField(blank=True, null=True)
    ismoderator = models.BooleanField(blank=True, null=True)
    confirm_code = models.TextField(blank=True, null=True)
    is_teacher = models.BooleanField()
    is_puppet = models.BooleanField()
    has_teacher = models.TextField(blank=True, null=True)
    last_active = models.DateTimeField(blank=True, null=True)
    id = models.AutoField(primary_key=True)

    class Meta:
        managed = False
        db_table = "users"
        verbose_name_plural = "users"

    def __str__(self):
        return f"{self.username}"
