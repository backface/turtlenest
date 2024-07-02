class LegacyDbRouter(object):
    def db_for_read(self, model, **hints):
        """reading model based on params"""
        if not hasattr(model, "Meta"):
            return None
        return getattr(model.Meta, "_db", None)

    def db_for_write(self, model, **hints):
        """writing model based on params"""
        if not hasattr(model, "Meta"):
            return None
        return getattr(model.Meta, "_db", None)
