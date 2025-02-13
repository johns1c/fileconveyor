from .transporter import *
from .transporter_s3 import TransporterS3


TRANSPORTER_CLASS = "TransporterCF"


class TransporterCF(TransporterS3):


    name              = 'CF'
    valid_settings    = ImmutableSet(["access_key_id", "secret_access_key", "bucket_name", "distro_domain_name", "bucket_prefix"])
    required_settings = ImmutableSet(["access_key_id", "secret_access_key", "bucket_name", "distro_domain_name"])


    def __init__(self, settings, callback, error_callback, parent_logger=None):
        return TransporterS3.__init__(self, settings, callback, error_callback, parent_logger)


    def alter_url(self, url):
        return url.replace(
            self.settings["bucket_prefix"] + self.settings["bucket_name"] + ".s3.amazonaws.com",
            self.settings["distro_domain_name"]
        )


def create_distribution(access_key_id, secret_access_key, origin, comment="", cnames=None):
    import time
    from boto.cloudfront import CloudFrontConnection

    """utility function to create a new distribution"""
    c = CloudFrontConnection(
        access_key_id,
        secret_access_key
    )
    d = c.create_distribution(origin, True, '', cnames, comment)
    print("""Created distribution
    - domain name: %s
    - origin: %s
    - status: %s
    - comment: %s
    - id: %s

    Over the next few minutes, the distribution will become active. This
    function will keep running until that happens.
    """ % (d.domain_name, d.config.origin, d.status, d.config.comment, d.id))

    # Keep polling CloudFront every 5 seconds until the status changes from
    # "InProgress" to (hopefully) "Deployed".
    print("\n")
    id = d.id
    while d.status == "InProgress":
        d = c.get_distribution_info(id)
        print(".")
        time.sleep(5)
    print("\nThe distribution has been deployed!")
