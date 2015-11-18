from rhumba.client import RhumbaClient

def build(build):
    c = RhumbaClient()

    print build

    return c.queue('sideloader', 'build', {})

def pushRelease(build_id, flow, scheduled=None):
    pass

def getClusterStatus():
    return RhumbaClient().clusterStatus()
