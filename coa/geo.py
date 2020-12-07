# -*- coding: utf-8 -*-
""" Project : PyCoA
Date :    april-november 2020
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pycoa.fr
License: See joint LICENSE file

Module : coa.geo

About :
-------

Geo classes within the PyCoA framework.

GeoManager class provides translations between naming normalisations
of countries. It's based on the pycountry module.

GeoInfo class allow to add new fields to a pandas DataFrame about
statistical information for countries.

GeoRegion class helps returning list of countries in a specified region
"""

import warnings

import pycountry as pc
import pycountry_convert as pcc
import pandas as pd
import geopandas as gpd
import shapely
import requests
import bs4

from coa.tools import verb,kwargs_test,get_local_from_url
from coa.error import *

# ---------------------------------------------------------------------
# --- GeoManager class ------------------------------------------------
# ---------------------------------------------------------------------

class GeoManager():
    """GeoManager class definition. No inheritance from any other class.

    It should raise only CoaError and derived exceptions in case
    of errors (see pycoa.error)
    """

    _list_standard=['iso2',   # Iso2 standard, default
            'iso3',           # Iso3 standard
            'name',           # Standard name ( != Official, caution )
            'num']            # Numeric standard

    _list_db=[None,'jhu','worldometers','owid'] # first is default
    _list_output=['list','dict','pandas'] # first is default

    _standard = None # currently used normalisation standard

    def __init__(self,standard=_list_standard[0]):
        """ __init__ member function, with default definition of
        the used standard. To get the current default standard,
        see get_list_standard()[0].
        """
        verb("Init of GeoManager()")
        self.set_standard(standard)
        self._gr=GeoRegion()

    def get_list_standard(self):
        """ return the list of supported standard name of countries.
        First one is default for the class
        """
        return self._list_standard

    def get_list_output(self):
        """ return supported list of output type. First one is default
        for the class
        """
        return self._list_output

    def get_list_db(self):
        """ return supported list of database name for translation of
        country names to standard.
        """
        return self._list_db

    def get_standard(self):
        """ return current standard use within the GeoManager class
        """
        return self._standard

    def set_standard(self,standard):
        """
        set the working standard type within the GeoManager class.
        The standard should meet the get_list_standard() requirement
        """
        if not isinstance(standard,str):
            raise CoaTypeError('GeoManager error, the standard argument'
                ' must be a string')
        if standard not in self.get_list_standard():
            raise CoaKeyError('GeoManager.set_standard error, "'+\
                                    standard+' not managed. Please see '\
                                    'get_list_standard() function')
        self._standard=standard
        return self.get_standard()

    def to_standard(self, w, **kwargs):
        """Given a list of string of locations (countries), returns a
        normalised list according to the used standard (defined
        via the setStandard() or __init__ function. Current default is iso2.

        Arguments
        -----------------
        first arg        --  w, list of string of locations (or single string)
                             to convert to standard one

        output           -- 'list' (default), 'dict' or 'pandas'
        db               -- database name to help conversion.
                            Default : None, meaning best effort to convert.
                            Known database : jhu, wordometer... 
                            See get_list_db() for full list of known db for 
                            standardization
        interpret_region -- Boolean, default=False. If yes, the output should
                            be only 'list'.
        """

        kwargs_test(kwargs,['output','db','interpret_region'],'Bad args used in the to_standard() function.')

        output=kwargs.get('output',self.get_list_output()[0])
        if output not in self.get_list_output():
            raise CoaKeyError('Incorrect output type. See get_list_output()'
                ' or help.')

        db=kwargs.get('db',self.get_list_db()[0])
        if db not in self.get_list_db():
            raise CoaDbError('Unknown database "'+db+'" for translation to '
                'standardized location names. See get_list_db() or help.')

        interpret_region=kwargs.get('interpret_region',False)
        if not isinstance(interpret_region,bool):
            raise CoaTypeError('The interpret_region argument is a boolean, '
                'not a '+str(type(interpret_region)))

        if interpret_region==True and output!='list':
            raise CoaKeyError('The interpret_region True argument is incompatible '
                'with non list output option.')

        if isinstance(w,str):
            w=[w]
        elif not isinstance(w,list):
            raise CoaTypeError('Waiting for str, list of str or pandas'
                'as input of get_standard function member of GeoManager')

        w=[v.title() for v in w] # capitalize first letter of each name

        w0=w.copy()

        if db:
            w=self.first_db_translation(w,db)

        n=[] # will contain standardized name of countries (if possible)

        #for c in w:
        while len(w)>0:
            c=w.pop(0)
            if type(c)==int:
                c=str(c)
            elif type(c)!=str:
                raise CoaTypeError('Locations should be given as '
                    'strings or integers only')
            if (c in self._gr.get_region_list()) and interpret_region == True:
                w=self._gr.get_countries_from_region(c)+w
            else:
                if len(c)==0:
                    n1='' #None
                else:
                    try:
                        n0=pc.countries.lookup(c)
                    except LookupError:
                        try:
                            nf=pc.countries.search_fuzzy(c)
                            if len(nf)>1:
                                warnings.warn('Caution. More than one country match the key "'+\
                                c+'" : '+str([ (k.name+', ') for k in nf])+\
                                ', using first one.\n')
                            n0=nf[0]
                        except LookupError:
                            raise CoaLookupError('No country match the key "'+c+'". Error.')
                        except Exception as e1:
                            raise CoaNotManagedError('Not managed error '+type(e1))
                    except Exception as e2:
                        raise CoaNotManagedError('Not managed error'+type(e1))

                    if self._standard=='iso2':
                        n1=n0.alpha_2
                    elif self._standard=='iso3':
                        n1=n0.alpha_3
                    elif self._standard=='name':
                        n1=n0.name
                    elif self._standard=='num':
                        n1=n0.numeric
                    else:
                        raise CoaKeyError('Current standard is '+self._standard+\
                            ' which is not managed. Error.')

                n.append(n1)

        if output=='list':
            return n
        elif output=='dict':
            return dict(zip(w0, n))
        elif output=='pandas':
            return pd.DataFrame({'inputname':w0,self._standard:n})
        else:
            return None # should not be here

    def first_db_translation(self,w,db):
        """ This function helps to translate from country name to
        standard for specific databases. It's the first step
        before final translation.

        One can easily add some database support adding some new rules
        for specific databases
        """
        translation_dict={}
        # Caution : keys need to be in title mode, i.e. first letter capitalized
        if db=='jhu':
            translation_dict.update({\
                "Congo (Brazzaville)":"Republic of the Congo",\
                "Congo (Kinshasa)":"COD",\
                "Korea, South":"KOR",\
                "Taiwan*":"Taiwan",\
                "Laos":"LAO",\
                "West Bank And Gaza":"PSE",\
                "Burma":"Myanmar",\
                "Iran":"IRN",\
                "Diamond Princess":"",\
                "Ms Zaandam":"",\
                    })  # last two are names of boats
        elif db=='worldometers':
            translation_dict.update({\
                "Dr Congo":"COD",\
                "Congo":"COG",\
                "Iran":"IRN",\
                "South Korea":"KOR",\
                "North Korea":"PRK",\
                "Czech Republic (Czechia)":"CZE",\
                "Laos":"LAO",\
                "Sao Tome & Principe":"STP",\
                "Channel Islands":"JEY",\
                "St. Vincent & Grenadines":"VCT",\
                "U.S. Virgin Islands":"VIR",\
                "Saint Kitts & Nevis":"KNA",\
                "Faeroe Islands":"FRO",\
                "Caribbean Netherlands":"BES",\
                "Wallis & Futuna":"WLF",\
                "Saint Pierre & Miquelon":"SPM",\
                "Sint Maarten":"SXM",\
                } )
        elif db=='owid':
            translation_dict.update({\
                    "Bonaire Sint Eustatius And Saba":"BES",\
                    "Cape Verde":"CPV",\
                    "Democratic Republic Of Congo":"COD",\
                    "Faeroe Islands":"FRO",\
                    "Laos":"LAO",\
                    "South Korea":"KOR",\
                    "Swaziland":"SWZ",\
                    "United States Virgin Islands":"VIR",\
                    "Iran":"IRN",\
                })
        return [translation_dict.get(k,k) for k in w]

# ---------------------------------------------------------------------
# --- GeoInfo class ---------------------------------------------------
# ---------------------------------------------------------------------

class GeoInfo():
    """GeoInfo class definition. No inheritance from any other class.

    It should raise only CoaError and derived exceptions in case
    of errors (see pycoa.error)
    """

    _list_field={\
        'continent_code':'pycountry_convert (https://pypi.org/project/pycountry-convert/)',\
        'continent_name':'pycountry_convert (https://pypi.org/project/pycountry-convert/)' ,\
        'country_name':'pycountry_convert (https://pypi.org/project/pycountry-convert/)' ,\
        'population':'https://www.worldometers.info/world-population/population-by-country/',\
        'area':'https://www.worldometers.info/world-population/population-by-country/',\
        'fertility':'https://www.worldometers.info/world-population/population-by-country/',\
        'median_age':'https://www.worldometers.info/world-population/population-by-country/',\
        'urban_rate':'https://www.worldometers.info/world-population/population-by-country/',\
        #'geometry':'https://github.com/johan/world.geo.json/',\
        'geometry':'http://thematicmapping.org/downloads/world_borders.php and https://github.com/johan/world.geo.json/',\
        'region_code_list':'https://en.wikipedia.org/wiki/List_of_countries_by_United_Nations_geoscheme',\
        'region_name_list':'https://en.wikipedia.org/wiki/List_of_countries_by_United_Nations_geoscheme',\
        'capital':'https://en.wikipedia.org/wiki/List_of_countries_by_United_Nations_geoscheme',\
        'flag':'https://github.com/linssen/country-flag-icons/blob/master/countries.json',\
        }

    _data_geometry = pd.DataFrame()
    _data_population = pd.DataFrame()
    _data_flag = pd.DataFrame()

    def __init__(self,gm=0):
        """ __init__ member function.
        """
        verb("Init of GeoInfo()")
        if gm != 0:
            self._gm=gm
        else:
            self._gm=GeoManager()

        self._grp=self._gm._gr.get_pandas()

    def get_list_field(self):
        """ return the list of supported additionnal fields available
        """
        return sorted(list(self._list_field.keys()))

    def get_source(self,field=None):
        """ return the source of the information provided for a given
        field.
        """
        if field==None:
            return self._list_field
        elif field not in self.get_list_field():
            raise CoaKeyError('The field "'+str(field)+'" is not '
                'a supported field of GeoInfo(). Please see help or '
                'the get_list_field() output.')
        return field+' : '+self._list_field[field]

    def add_field(self,**kwargs):
        """ this is the main function of the GeoInfo class. It adds to
        the input pandas dataframe some fields according to
        the geofield field of input.
        The return value is the pandas dataframe.

        Arguments :
        field    -- should be given as a string of list of strings and
                    should be valid fields (see get_list_field() )
                    Mandatory.
        input    -- provide the input pandas dataframe. Mandatory.
        geofield -- provide the field name in the pandas where the
                    location is stored. Default : 'location'
        overload -- Allow to overload a field. Boolean value.
                    Default : False
        """

        # --- kwargs analysis ---

        kwargs_test(kwargs,['field','input','geofield','overload'],
            'Bad args used in the add_field() function.')

        p=kwargs.get('input',None) # the panda
        if not isinstance(p,pd.DataFrame):
            raise CoaTypeError('You should provide a valid input pandas'
                ' DataFrame as input. See help.')
        p=p.copy()

        overload=kwargs.get('overload',False)
        if not isinstance(overload,bool):
            raise CoaTypeError('The overload option should be a boolean.')

        fl=kwargs.get('field',None) # field list
        if fl == None:
            raise CoaKeyError('No field given. See help.')
        if not isinstance(fl,list):
            fl=[fl]
        if not all(f in self.get_list_field() for f in fl):
            raise CoaKeyError('All fields are not valid or supported '
                'ones. Please see help of get_list_field()')

        if not overload and not all(f not in p.columns.tolist() for f in fl):
            raise CoaKeyError('Some fields already exist in you panda '
                'dataframe columns. You may set overload to True.')

        geofield=kwargs.get('geofield','location')

        if not isinstance(geofield,str):
            raise CoaTypeError('The geofield should be given as a '
                'string.')
        if geofield not in p.columns.tolist():
            raise CoaKeyError('The geofield "'+geofield+'" given is '
                'not a valid column name of the input pandas dataframe.')

        self._gm.set_standard('iso2')
        countries_iso2=self._gm.to_standard(p[geofield].tolist())
        self._gm.set_standard('iso3')
        countries_iso3=self._gm.to_standard(p[geofield].tolist())

        p['iso2_tmp']=countries_iso2
        p['iso3_tmp']=countries_iso3

        # --- loop over all needed fields ---
        for f in fl:
            if f in p.columns.tolist():
                p=p.drop(f,axis=1)
            # ----------------------------------------------------------
            if f == 'continent_code':
                p[f] = [pcc.country_alpha2_to_continent_code(k) for k in countries_iso2]
            # ----------------------------------------------------------
            elif f == 'continent_name':
                p[f] = [pcc.convert_continent_code_to_continent_name( \
                    pcc.country_alpha2_to_continent_code(k) ) for k in countries_iso2 ]
            # ----------------------------------------------------------
            elif f == 'country_name':
                p[f] = [pcc.country_alpha2_to_country_name(k) for k in countries_iso2]
            # ----------------------------------------------------------
            elif f in ['population','area','fertility','median_age','urban_rate']:
                if self._data_population.empty:

                    field_descr=( (0,'','idx'),
                        (1,'Country','country'),
                        (2,'Population','population'),
                        (6,'Land Area','area'),
                        (8,'Fert','fertility'),
                        (9,'Med','median_age'),
                        (10,'Urban','urban_rate'),
                        ) # containts tuples with position in table, name of column, new name of field

                    # get data with cache ok for about 1 month
                    self._data_population = pd.read_html(get_local_from_url('https://www.worldometers.info/world-population/population-by-country/',30e5) ) [0].iloc[:,[x[0] for x in field_descr]]

                    # test that field order hasn't changed in the db
                    if not all (col.startswith(field_descr[i][1]) for i,col in enumerate(self._data_population.columns) ):
                        raise CoaDbError('The worldometers database changed its field names. '
                            'The GeoInfo should be updated. Please contact developers.')

                    # change field name
                    self._data_population.columns = [x[2] for x in field_descr]

                    # standardization of country name
                    self._data_population['iso3_tmp2']=\
                        self._gm.to_standard(self._data_population['country'].tolist(),\
                        db='worldometers')

                p=p.merge(self._data_population[["iso3_tmp2",f]],how='left',\
                        left_on='iso3_tmp',right_on='iso3_tmp2',\
                        suffixes=('','_tmp')).drop(['iso3_tmp2'],axis=1)
            # ----------------------------------------------------------
            elif f in ['region_code_list','region_name_list']:

                if f == 'region_code_list':
                    ff = 'region'
                elif f == 'region_name_list':
                    ff = 'region_name'

                p[f]=p.merge(self._grp[['iso3',ff]],how='left',\
                    left_on='iso3_tmp',right_on='iso3',\
                    suffixes=('','_tmp')) \
                    .groupby('iso3_tmp')[ff].apply(list).to_list()
            # ----------------------------------------------------------
            elif f in ['capital']:
                p[f]=p.merge(self._grp[['iso3',f]].drop_duplicates(), \
                    how='left',left_on='iso3_tmp',right_on='iso3',\
                    suffixes=('','_tmp'))[f]

            # ----------------------------------------------------------
            elif f == 'geometry':
                if self._data_geometry.empty:
                    #geojsondatafile = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json'
                    #self._data_geometry = gpd.read_file(get_local_from_url(geojsondatafile,0,'.json'))[["id","geometry"]]
                    world_geometry_url_zipfile='http://thematicmapping.org/downloads/TM_WORLD_BORDERS_SIMPL-0.3.zip' # too much simplified version ?
                    # world_geometry_url_zipfile='http://thematicmapping.org/downloads/TM_WORLD_BORDERS-0.3.zip' # too precize version ? 
                    self._data_geometry = gpd.read_file('zip://'+get_local_from_url(world_geometry_url_zipfile,0,'.zip'))[['ISO3','geometry']]
                    self._data_geometry.columns=["id_tmp","geometry"]

                    # About Sudan and South Sudan, not properly managed by this database
                    self._data_geometry=self._data_geometry.append({'id_tmp':'SSD','geometry':None},ignore_index=True) # adding the SSD row
                    for newc in ['SSD','SDN']:
                        newgeo=gpd.read_file(get_local_from_url('https://github.com/johan/world.geo.json/raw/master/countries/'+newc+'.geo.json'))
                        self._data_geometry.loc[self._data_geometry.id_tmp==newc,'geometry']=newgeo.loc[newgeo.id==newc,'geometry'][0]

                p=p.merge(self._data_geometry,how='left',\
                    left_on='iso3_tmp',right_on='id_tmp',\
                    suffixes=('','_tmp')).drop(['id_tmp'],axis=1)

            # -----------------------------------------------------------
            elif f == 'flag':
                if self._data_flag.empty:
                    self._data_flag = pd.read_json(get_local_from_url('https://github.com/linssen/country-flag-icons/raw/master/countries.json',0))
                    self._data_flag['flag_url']='http:'+self._data_flag['file_url']

                p=p.merge(self._data_flag[['alpha3','flag_url']],how='left',\
                    left_on='iso3_tmp',right_on='alpha3').drop(['alpha3'],axis=1)

        return p.drop(['iso2_tmp','iso3_tmp'],axis=1,errors='ignore')

# ---------------------------------------------------------------------
# --- GeoRegion class -------------------------------------------------
# ---------------------------------------------------------------------

class GeoRegion():
    """GeoRegion class definition. Does not inheritate from any other
    class.

    It should raise only CoaError and derived exceptions in case
    of errors (see pycoa.error)
    """

    _source_dict={"UN_M49":"https://en.wikipedia.org/w/index.php?title=UN_M49&oldid=986603718", # pointing the previous correct ref . https://en.wikipedia.org/wiki/UN_M49",\
        "GeoScheme":"https://en.wikipedia.org/wiki/List_of_countries_by_United_Nations_geoscheme",
        "European Union":"https://europa.eu/european-union/about-eu/countries/member-countries_en",
        "G7":"https://en.wikipedia.org/wiki/Group_of_Seven",
        "G8":"https://en.wikipedia.org/wiki/Group_of_Eight",
        "G20":"https://en.wikipedia.org/wiki/G20",
        "G77":"https://www.g77.org/doc/members.html",
        "OECD":"https://en.wikipedia.org/wiki/OECD"}

    _region_dict={}
    _p_gs = pd.DataFrame()

    def __init__(self,):
        """ __init__ member function.
        """
        #if 'XK' in self._country_list:
        #    del self._country_list['XK'] # creates bugs in pycountry and is currently a contested country as country


        # --- get the UN M49 information and organize the data in the _region_dict

        verb("Init of GeoRegion()")

        p_m49=pd.read_html(get_local_from_url(self._source_dict["UN_M49"],0))[1]

        p_m49.columns=['code','region_name']
        p_m49['region_name']=[r.split('(')[0].rstrip() for r in p_m49.region_name]  # suppress information in parenthesis in region name
        p_m49.set_index('code')

        self._region_dict.update(p_m49.to_dict('split')['data'])
        self._region_dict.update({  "UE":"European Union",
                                    "G7":"G7",
                                    "G8":"G8",
                                    "G20":"G20",
                                    "OECD":"Oecd",
                                    "G77":"G77",
                                    })  # add UE for other analysis


        # --- get the UnitedNation GeoScheme and organize the data
        p_gs=pd.read_html(get_local_from_url(self._source_dict["GeoScheme"],0))[0]
        p_gs.columns=['country','capital','iso2','iso3','num','m49']

        idx=[]
        reg=[]
        cap=[]

        for index, row in p_gs.iterrows():
            if row.iso3 != '–' : # meaning a non standard iso in wikipedia UN GeoScheme
                for r in row.m49.replace(" ","").split('<'):
                    idx.append(row.iso3)
                    reg.append(int(r))
                    cap.append(row.capital)
        self._p_gs=pd.DataFrame({'iso3':idx,'capital':cap,'region':reg})
        self._p_gs=self._p_gs.merge(p_m49,how='left',left_on='region',\
                            right_on='code').drop(["code"],axis=1)
    
    def get_source(self):
        return self._source_dict

    def get_region_list(self):
        return list(self._region_dict.values())

    def get_countries_from_region(self,region):
        """ it returns a list of countries for the given region name.
        The standard used is iso3. To convert to another standard,
        use the GeoManager class.
        """

        if type(region) != str:
            raise CoaKeyError("The given region is not a str type.")

        region=region.title()  # if not properly capitalized

        if region not in self.get_region_list():
            raise CoaKeyError('The given region "'+str(region)+'" is unknown.')

        clist=[]

        if region=='European Union':
            clist=['AUT','BEL','BGR','CYP','CZE','DEU','DNK','EST',\
                        'ESP','FIN','FRA','GRC','HRV','HUN','IRL','ITA',\
                        'LTU','LUX','LVA','MLT','NLD','POL','PRT','ROU',\
                        'SWE','SVN','SVK']
        elif region=='G7':
            clist=['DEU','CAN','USA','FRA','ITA','JAP','GBR']
        elif region=='G8':
            clist=['DEU','CAN','USA','FRA','ITA','JAP','GBR','RUS']
        elif region=='G20':
            clist=['ZAF','SAU','ARG','AUS','BRA','CAN','CHN','KOR','USA',\
                'IND','IDN','JAP','MEX','GBR','RUS','TUR',\
                'AUT','BEL','BGR','CYP','CZE','DEU','DNK','EST',\
                'ESP','FIN','FRA','GRC','HRV','HUN','IRL','ITA',\
                'LTU','LUX','LVA','MLT','NLD','POL','PRT','ROU',\
                'SWE','SVN','SVK']
        elif region=='Oecd': # OCDE in french
            clist=['DEU','AUS','AUT','BEL','CAN','CHL','COL','KOR','DNK',\
                'ESP','EST','USA','FIN','FRA','GRC','HUN','IRL','ISL','ISR',\
                'ITA','JAP','LVA','LTU','LUX','MEX','NOR','NZL','NLD','POL',\
                'PRT','SVK','SVN','SWE','CHE','GBR','CZE','TUR']
        elif region=='G77':
            clist=['AFG','DZA','AGO','ATG','ARG','AZE','BHS','BHR','BGD','BRB','BLZ',
                'BEN','BTN','BOL','BWA','BRA','BRN','BFA','BDI','CPV','KHM','CMR',
                'CAF','TCD','CHL','CHN','COL','COM','COG','CRI','CIV','CUB','PRK',
                'COD','DJI','DMA','DOM','ECU','EGY','SLV','GNQ','ERI','SWZ','ETH',
                'FJI','GAB','GMB','GHA','GRD','GTM','GIN','GNB','GUY','HTI','HND',
                'IND','IDN','IRN','IRQ','JAM','JOR','KEN','KIR','KWT','LAO','LBN',
                'LSO','LBR','LBY','MDG','MWI','MYS','MDV','MLI','MHL','MRT','MUS',
                'FSM','MNG','MAR','MOZ','MMR','NAM','NRU','NPL','NIC','NER','NGA',
                'OMN','PAK','PAN','PNG','PRY','PER','PHL','QAT','RWA','KNA','LCA',
                'VCT','WSM','STP','SAU','SEN','SYC','SLE','SGP','SLB','SOM','ZAF',
                'SSD','LKA','PSE','SDN','SUR','SYR','TJK','THA','TLS','TGO','TON',
                'TTO','TUN','TKM','UGA','ARE','TZA','URY','VUT','VEN','VNM','YEM',
                'ZMB','ZWE']
        else:
            clist=self._p_gs[self._p_gs['region_name']==region]['iso3'].to_list()

        return sorted(clist)

    def get_pandas(self):
        return self._p_gs


# ---------------------------------------------------------------------
# --- GeoCountryclass -------------------------------------------------
# ---------------------------------------------------------------------

class GeoCountry():
    """GeoCountry class definition.
    This class provides functions for specific countries and their states / departments / regions,
    and their geo properties (geometry, population if available, etc.)
    
    The list of supported countries is given by get_list_countries() function """

    # Assuming zip file here
    _country_info_dict = {'FRA':'https://datanova.laposte.fr/explore/dataset/geoflar-departements-2015/download/?format=shp&timezone=Europe/Berlin&lang=fr',\
                    }

    _source_dict = {'FRA':{'Basics':_country_info_dict['FRA'],\
                    'Subregion Flags':'http://sticker-departement.com/',\
                    'Region Flags':'https://fr.wikipedia.org/w/index.php?title=R%C3%A9gion_fran%C3%A7aise&oldid=177269957'},\
                    }

    def __init__(self,country=None):
        """ __init__ member function. 
        Must give as arg the country to deal with, as a valid ISO3 string
        """
        self._country=country
        if country == None:
            return None

        if not country in self.get_list_countries():
            raise CoaKeyError("Country "+str(country)+" not supported. Please see get_list_countries() and help. ")

        self._country_data_region=None
        self._country_data_subregion=None

        url=self._country_info_dict[country]
        self._country_data = gpd.read_file('zip://'+get_local_from_url(url,0,'.zip')) # under the hypothesis this is a zip file

        # country by country, adapt the read file informations

        # --- 'FRA' case ---------------------------------------------------------------------------------------
        if self._country=='FRA':

            # adding a flag for subregion (departements)
            self._country_data['flag_subregion']=self._source_dict['FRA']['Subregion Flags']+'img/dept/sticker_plaque_immat_'+\
                self._country_data['code_dept']+'_'+\
                [n.lower() for n in self._country_data['nom_dept']]+'_moto.png' # picture of a sticker for motobikes, not so bad...

            # Reading information to get region flags and correct names of regions
            f_reg_flag=open(get_local_from_url(self._source_dict['FRA']['Region Flags'],0), 'r')
            content_reg_flag = f_reg_flag.read()
            f_reg_flag.close()
            soup_reg_flag = bs4.BeautifulSoup(content_reg_flag,'lxml')
            for img in soup_reg_flag.find_all('img'):  # need to convert <img tags to src content for pandas_read 
                src=img.get('src')
                if src[0] == '/':
                    src='http:'+src
                img.replace_with(src)

            tabs_reg_flag=pd.read_html(str(soup_reg_flag)) # pandas read the modified html
            metropole=tabs_reg_flag[5][["Logo","Dénomination","Code INSEE[5]"]]  # getting 5th table, and only usefull columns
            ultramarin=tabs_reg_flag[6][["Logo","Dénomination","Code INSEE[5]"]] # getting 6th table
            p_reg_flag=pd.concat([metropole,ultramarin]).rename(columns={"Code INSEE[5]":"code_region",\
                                                                        "Logo":"flag_region",\
                                                                        "Dénomination":"name_region"})

            p_reg_flag=p_reg_flag[pd.notnull(p_reg_flag["code_region"])]  # select only valid rows
            p_reg_flag["name_region"]=[ n.split('[')[0] for n in p_reg_flag["name_region"] ] # remove footnote [k] index from wikipedia
            p_reg_flag["code_region"]=[ str(int(c)).zfill(2) for c in p_reg_flag["code_region"] ] # convert to str for merge the code, adding 1 leading 0 if needed

            self._country_data=self._country_data.merge(p_reg_flag,how='left',\
                    left_on='code_reg',right_on='code_region') # merging with flag and correct names
        
            # standardize name for region, subregion
            self._country_data.rename(columns={\
                'code_dept':'code_subregion',\
                'nom_dept':'name_subregion',\
                'nom_chf':'town_subregion',\
                },inplace=True)

            self._country_data.drop(['id_geofla','code_reg','nom_reg','x_chf_lieu','y_chf_lieu','x_centroid','y_centroid'],axis=1,inplace=True) # removing some column without interest 

            # Moving DROM-COM near hexagon
            list_translation={"GUADELOUPE":(63,23),
                             "MARTINIQUE":(63,23),
                             "GUYANE":(50,35),
                             "REUNION":(-51,60),
                             "MAYOTTE":(-38,51.5)}
            tmp = []
            for index, poi in self._country_data.iterrows():
                x=0
                y=0
                w=self._country_data.loc[index,"name_subregion"]
                if w in list_translation.keys():
                    x=list_translation[w][0]
                    y=list_translation[w][1]
                g = shapely.affinity.translate(self._country_data.loc[index, 'geometry'], xoff=x, yoff=y)
                tmp.append(g)
            self._country_data['geometry']=tmp

            # Add Ile de France zoom 
            idf_translation=(-6.5,-5)
            idf_scale=5
            idf_center=(-4,44)
            tmp = []
            for index, poi in self._country_data.iterrows():
                g=self._country_data.loc[index, 'geometry']
                if self._country_data.loc[index,'code_subregion'] in ['75','92','93','94']:
                    g2=shapely.affinity.scale(shapely.affinity.translate(g,xoff=idf_translation[0],yoff=idf_translation[1]),\
                                            xfact=idf_scale,yfact=idf_scale,origin=idf_center)
                    g=shapely.ops.unary_union([g,g2])
                tmp.append(g)
            self._country_data['geometry']=tmp

    def get_source(self):
        """ Return informations about URL sources
        """
        return self._source_dict

    def get_country(self):
        """ Return the current country used.
        """
        return self._country

    def get_list_countries(self):
        """ This function returns back the list of supported countries
        """
        return sorted(list(self._country_info_dict.keys()))

    def is_init(self):
        """Test if the country is initialized. Return True if it is. False if not.
        """
        if self.get_country() != None:
            return True
        else:
            return False

    def test_is_init(self):
        """Test if the country is initialized. If not, raise a CoaDbError.
        """
        if self.is_init():
            return True
        else:
            raise CoaDbError("The country is not set. Use a constructor with non empty country string.")

    def get_region_list(self):
        """ Return the list of available regions with code, name and geometry
        """
        cols=[c for c in self.get_list_properties() if '_region' in c]
        cols.append('geometry')
        return self.get_data(True)[cols]

    def get_subregion_list(self):
        """ Return the list of available subregions with code, name and geometry
        """
        cols=[c for c in self.get_list_properties() if '_subregion' in c ]
        cols.append('geometry')
        return self.get_data()[cols]

    def get_list_properties(self):
        """Return the list of available properties for the current country
        """
        if self.test_is_init():
            return sorted(self._country_data.columns.to_list())

    def get_data(self,region_version=False):
        """Return the whole geopandas data
        """
        if self.test_is_init():
            if region_version:
                if not isinstance(self._country_data_region,pd.DataFrame): # i.e. is None
                    col_reg=[c for c in self._country_data.columns.tolist() if '_region' in c]
                    col=col_reg.copy()
                    col.append('code_subregion') # to get the list of subregion in region
                    col.append('geometry') # to merge the geometry of subregions
                    pr=self._country_data[col].copy()
                    pr['code_subregion']=pr.code_subregion.apply(lambda x: [x])
                    self._country_data_region=pr.dissolve(by=col_reg,aggfunc='sum').sort_values(by='code_region').reset_index()
                return self._country_data_region
            else:
                if not isinstance(self._country_data_subregion,pd.DataFrame): #i.e. is None
                    self._country_data_subregion=self._country_data.sort_values(by='code_subregion')
                return self._country_data_subregion

    def add_info(self,**kwargs):
        """Return a the data pandas.Dataframe with an additionnal column with property prop.

        Arguments : 
        input        : pandas.Dataframe object. Mandatory.
        field        : field of properties to add. Should be within the get_list_prop() list. Mandatory.
        input_key    : input geo key of the input pandas dataframe. Default  'where'
        geofield     : internal geo field to make the merge. Default 'code_subregion' 
        region_merging : Boolean value. Default False, except if the geofield contains '_region'. 
                       If True, the merge between input dans GeoCountry data is done within the 
                       region version of the data, not the subregion data which is the default 
                       behavious.
        overload   : Allow to overload a field. Boolean value. Default : False
        """

        # Test of args
        kwargs_test(kwargs,['input','field','input_key','geofield','geotype','overload'],
            'Bad args used in the add_field() function.')

        # Testing input
        data=kwargs.get('input',None) # the panda
        if not isinstance(data,pd.DataFrame):
            raise CoaTypeError('You should provide a valid input pandas'
                ' DataFrame as input. See help.')
        data=data.copy()

        # Testing input_key
        input_key=kwargs.get('input_key','where')
        if not isinstance(input_key,str):
            raise CoaTypeError('The input_key should be given as a string.')
        if input_key not in data.columns.tolist():
            raise CoaKeyError('The input_key "'+input_key+'" given is '
                'not a valid column name of the input pandas dataframe.')

        # Testing geofield
        geofield=kwargs.get('geofield','code_subregion')
        if not isinstance(geofield,str):
            raise CoaTypeError('The geofield should be given as a string.')
        if geofield not in self._country_data.columns.tolist():
            raise CoaKeyError('The geofield "'+geofield+'" given is '
                'not a valid column name of the available data. '
                'See get_list_properties() for valid fields.')

        region_merging=kwargs.get('region_merging',None)
        if region_merging == None:
            if '_region' in geofield:
                region_merging=True 
            else:
                region_merging=False

        if not instance(region_merging,bool):
            raise CoaKeyError('The region_mergin key should be boolean. See help.')

        # Testing fields
        prop=kwargs.get('field',None) # field list
        if prop == None:
            raise CoaKeyError('No field given. See help.')
        if not isinstance(prop,list):
            prop=[prop] # make the prop input a list if needed

        if not all(isinstance(p, str) for p in prop):
            raise CoaTypeError("Each property should be a string whereas "+str(prop)+" is not a list of string.")

        if not all(p in self.get_list_properties() for p in prop):
            raise CoaKeyError("The property "+prop+" is not available for country "+self.get_country()+".")

        # Testing overload 
        overload=kwargs.get('overload',False)
        if not isinstance(overload,bool):
            raise CoaTypeError('The overload option should be a boolean.')

        if not overload and not all(p not in data.columns.tolist() for p in prop):
            raise CoaKeyError('Some fields already exist in you panda '
                'dataframe columns. You may set overload to True.')

        # Is the oject properly initialized ?
        self.test_is_init()
        
        # Now let's go for merging
        prop.append('code_subregion')
        return data.merge(self.get_data(region_merging)[prop],how='left',left_on=input_key,\
                            right_on=geofield)
