import datetime as dt


def year(request):
    today = dt.datetime.today()
    return {'year':today.year}