import calendar
import datetime
from zeep import Client
import requests
from pg import DB

def selectDate():
    dateStr = str(input('Input a date [YYYY-MM-DD]: '))
    return(datetime.datetime.strptime(dateStr, '%Y-%m-%d'))

def accessAPI(inList,un,pw,config):
    try:
        inList.append(blip.service.exportPerUserData(un,pw,config)) 
    except urllib.error.URLError: 
        LOGGER.info('In the error handler (URL error)...')            
        time.sleep(30)
        inList = accessAPI(inList,un,pw,config)
    except Exception: 
        LOGGER.info('In the error handler (SUDS error)...')            
        time.sleep(15)
        inList = accessAPI(inList,un,pw,config)
    return inList

def insertDF(df):
    try:    
        LOGGER.info('Uploading to PostgreSQL' + ', ' + datetime.datetime.now().strftime('%H:%M:%S'))     
        engine = create_engine()
        df.to_sql('raw_data',engine, schema = 'bluetooth', if_exists = 'append', index = False)
    except:
        LOGGER.info('Server Connection Error Handler' + ', '+ datetime.datetime.now().strftime('%H:%M:%S'))
        time.sleep(60)                    
        insertDF(df)
        
############### CODE BEGINS HERE ###############

if __name__ = '__main__':
    CONFIG = configparser.ConfigParser()
    CONFIG.read(ARGS.dbsetting)
    dbset = CONFIG['DBSETTINGS']
    
    FORMAT = '%(asctime)s %(name)-2s %(levelname)-2s %(message)s'
    logging.basicConfig(level=logging.INFO, format=FORMAT)
    LOGGER = logging.getLogger(__name__)

    api_settings = CONFIG['API']
    
    # Access the API using the suds package
    LOGGER.info('Going in!')
    try:
        blip = Client(api_settings['WSDLfile'])
    except urllib.error.URLError:
        time.sleep(10)
        blip = Client(api_settings['WSDLfile'])

    # Create a config object
    factory = blip.type_factory('ns0')
    config = factory.perUserDataExportConfiguration()
    config.live = False
    config.includeOutliers = True

    # list of all route segments
    allAnalyses = blip.service.getExportableAnalyses(un,pw)

    # Pull data from all relevant indices
    allInd = [0,1,4,6,7,8,9,10,11,12,13,14,15,16,58,59,60,61,70,71,74,75,76,77,78,79,80,81,82,83,84,85,86,87,95,96,97,98,99,149,150,151,181,182,183]
    allInd.extend(list(range(102,131)))
    objectList = []

    # Variables to edit
    start_year = 2017
    end_year = 2017
    start_month = 4
    end_month = 4
    
    years = list(range(start_year, end_year+1))
    
    months = list(range(start_month, end_month+1))

    for j, year, month in zip(allInd, years, months):
        if (month < 1):
            ndays = 0
        else:
            ndays = calendar.monthrange(year, month)[1]
            # ndays = 10
            LOGGER.info('Reading from: ' + str(allAnalyses[j].reportName) + ' y: ' + str(year) + ' m: ' + str(month))
            LOGGER.info(datetime.datetime.now().strftime('%H:%M:%S'))
            config.analysisId = allAnalyses[j].id
            config.startTime = datetime.datetime(year, month,1,0,0,0)

            days = list(range(ndays))
            ks = [0, 1, 2, 3, 4]
            
            for i, k in zip(days, ks):               
                if k == 0:                        
                    config.endTime = config.startTime + datetime.timedelta(hours = 8)
                elif k == 1:
                    config.endTime = config.startTime + datetime.timedelta(hours = 6)
                elif k == 2:
                    config.endTime = config.startTime + datetime.timedelta(hours = 5)
                elif k == 3:
                    config.endTime = config.startTime + datetime.timedelta(hours = 5)

                objectList = accessAPI(objectList,un,pw,config)

                if k == 0:
                    config.startTime = config.startTime + datetime.timedelta(hours = 8)
                elif k == 1:
                    config.startTime = config.startTime + datetime.timedelta(hours = 6)
                elif k == 2:
                    config.startTime = config.startTime + datetime.timedelta(hours = 5)
                elif k == 3:
                    config.startTime = config.startTime + datetime.timedelta(hours = 5)
                time.sleep(1)

            try:
                x = pd.DataFrame([Client.dict(item) for sublist in objectList for item in sublist])
                x = x.rename(columns={"userId" : "user_id", "analysisId" : "analysis_id", "measuredTime" : "measured_time", "measuredTimeNoFilter" : "measured_time_no_filter", \
                "startPointNumber" : "startpoint_number", "startPointName" : "startpoint_name", "endPointNumber" : "endpoint_number", "endPointName" : "endpoint_name", \
                "measuredTimeTimestamp" : "measured_timestamp", "outlierLevel" : "outlier_level", "deviceClass" : "device_class"})
                x.measured_timestamp = pd.to_datetime(x.measured_timestamp, infer_datetime_format=True, format='%m/%d/%Y  %H:%M:%S %p')
                insertDF(x)
            except:
                time.sleep(60)
                LOGGER.info('FAILED:' + str(allAnalyses[j].reportName) + ' y: ' + str(year) + ' m: ' + str(month))

        objectList = []


