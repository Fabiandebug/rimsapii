from frictionless import Package as BasePackage, system 


class Package(BasePackage):


    def to_sql(self, target, *, dialect):
        """Export package to SQL

        Parameters:
            target (any): SQL connection string of engine
            dialect (dict): SQL dialect

        Returns:
            SqlStorage: storage
        """
        storage = system.create_storage("sqldb", target, dialect=dialect)
        storage.write_package(self.to_copy(), force=True)
        return storage