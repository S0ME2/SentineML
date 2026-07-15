class DomainError(Exception):
    pass


class InvalidProjectData(DomainError):
    pass


class InvalidDatasetData(DomainError):
    pass


class InvalidModelData(DomainError):
    pass


class InvalidParameterData(DomainError):
    pass


class InvalidMetricData(DomainError):
    pass


class InvalidMetricDirectionData(DomainError):
    pass


class InvalidRunData(DomainError):
    pass


class InvalidRunState(DomainError):
    pass
