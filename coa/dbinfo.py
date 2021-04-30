# -*- coding: utf-8 -*-
"""Project : PyCoA - Copyright ©pycoa.fr
Date :    april 2020 - april 2021
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
License: See joint LICENSE file
Module : report
About
-----
This is the PyCoA rapport module it gives all available information concerning a database key words
"""
from coa.error import *

def generic_info(namedb, keys):
    '''
    Return information on the available keyswords for the database selected
    '''
    mydico = {}
    if namedb == 'spf':
        urlmaster1='https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/'
        urlmaster2=urlmaster1
        urlmaster3='https://www.data.gouv.fr/fr/datasets/donnees-relatives-aux-resultats-des-tests-virologiques-covid-19/'
        urlmaster5='https://www.data.gouv.fr/fr/datasets/donnees-relatives-aux-personnes-vaccinees-contre-la-covid-19-1'
        urlmaster4='https://www.data.gouv.fr/fr/datasets/indicateurs-de-suivi-de-lepidemie-de-covid-19/'
        urlmaster6='https://www.data.gouv.fr/fr/datasets/donnees-de-laboratoires-pour-le-depistage-indicateurs-sur-les-variants/'
        url1="https://www.data.gouv.fr/fr/datasets/r/63352e38-d353-4b54-bfd1-f1b3ee1cabd7"
        url2="https://www.data.gouv.fr/fr/datasets/r/6fadff46-9efd-4c53-942a-54aca783c30c"
        url3="https://www.data.gouv.fr/fr/datasets/r/406c6a23-e283-4300-9484-54e78c8ae675"
        url4="https://www.data.gouv.fr/fr/datasets/r/4acad602-d8b1-4516-bc71-7d5574d5f33e"
        url5="https://www.data.gouv.fr/fr/datasets/r/32a16487-3dd3-4326-9d2b-317e5a3b2daf"
        url6="https://www.data.gouv.fr/fr/datasets/r/16f4fd03-797f-4616-bca9-78ff212d06e8"
        spfdic = {
        'tot_dc':
        ['tot_dc:FILLIT',url1,urlmaster1],
        'cur_hosp':
        ['cur_hosp:FILLIT',url1,urlmaster1],
        'tot_rad':
        ['tot_rad:FILLIT',url1,urlmaster1],
        'cur_rea':
        ['cur_rea:FILLIT',url1,urlmaster1],
        'cur_idx_tx_incid':
        ['cur_idx_tx_incid:FILLIT',url2,urlmaster2],
        'cur_idx_R':
        ['cur_idx_R:FILLIT',url4,urlmaster4],
        'cur_idx_taux_occupation_sae':
        ['cur_idx_taux_occupation_sae:FILLIT',url4,urlmaster4],
        'cur_idx_tx_pos':
        ['cur_idx_tx_pos:FILLIT',url4,urlmaster4],
        'tot_vacc':
        ['tot_vacc: (nom initial n_cum_dose1)',url5,urlmaster5],
        'tot_vacc2':
        ['tot_vacc2: (nom initial n_cum_dose2)',url5,urlmaster5],
        'tot_incid_hosp':
        ['tot_incid_hosp: Nombre total de personnes hospitalisées',url2,urlmaster2],
        'tot_incid_rea':
        ['tot_incid_rea: Nombre total d\'admissions en réanimation',url2,urlmaster2],
        'tot_incid_rad':
        ['tot_incid_rad: Nombre total de  retours à domicile',url2,urlmaster2],
        'tot_incid_dc':
        ['tot_incid_dc: Nombre total de personnes  décédées',url2,urlmaster2],
        'tot_P':
        ['tot_P: Nombre total de tests positifs',url3,urlmaster3],
        'tot_T':
        ['tot_T: Nombre total de tests réalisés',url3,urlmaster3],
        'cur_idx_Prc_tests_PCR_TA_crible' :
        ['Prc_tests_PCR_TA_crible: % de tests PCR criblés parmi les PCR positives.',url6,urlmaster6],
        'cur_idx_Prc_susp_501Y_V1' :
        ['Prc_susp_501Y_V1: % de tests avec suspicion de variant 20I/501Y.V1 (UK).\n Royaume-Uni (UK): code Nexstrain= 20I/501Y.V1.',url6,urlmaster6],
        'cur_idx_Prc_susp_501Y_V2_3' :
        ['Prc_susp_501Y_V2_3: % de tests avec suspicion de variant 20H/501Y.V2 (ZA) ou 20J/501Y.V3 (BR).Afrique du Sud (ZA) : code Nexstrain= 20H/501Y.V2. Brésil (BR) : code Nexstrain= 20J/501Y.V3',url6,urlmaster6],
        'cur_idx_Prc_susp_IND' :
        ['Prc_susp_IND: % de tests avec une détection de variant mais non identifiable',url6,urlmaster6],
        'cur_idx_Prc_susp_ABS' :
        ['Prc_susp_ABS: % de tests avec une absence de détection de variant',url6,urlmaster6]
        }
        mydico = spfdic
    elif namedb == 'opencovid19':
        op19 = {
        'tot_deces':['tot_deces: total cumulé du nombre de décès au niveau national'],
        'tot_cas_confirmes':['tot_cas_confirmes: total cumulé du nombre de cas confirmes au niveau national'],
        'cur_reanimation':['cur_reanimation:  nombre de personnes en réanimation'],
        'cur_hospitalises':['cur_hospitalises: nombre de personnes en hospitalisation'],
        'tot_gueris':['tot_gueris: total cumulé du nombre de gueris au niveau national'],
        'tot_nouvelles_hospitalisations':['tot_nouvelles_hospitalisations: total cumulé du nombre d\'hospitalisation au niveau national'],
        'tot_nouvelles_reanimations':['tot_nouvelles_reanimations: tot_nouvelles_reanimations: total cumulé du nombre réanimations au niveau national'],
        'tot_depistes':['tot_depistes: total cumulé du nombre de personnes dépistées (testées par PCR) au niveau national'],
        }
        for k,v in op19.items():
            op19[k].append('https://raw.githubusercontent.com/opencovid19-fr/data/master/dist/chiffres-cles.csv')
            op19[k].append('https://github.com/opencovid19-fr/data')
        mydico = op19
    elif namedb == 'opencovid19national':
        op19nat = {
         'tot_deces':['tot_deces: total cumulé du nombre de décès'],
         'tot_cas_confirmes':['tot_cas_confirmes: total cumulé du nombre de cas confirmés'],
         'tot_cas_ehpad':['tot_cas_ehpad: total cumulé du nombre de cas en EHPAD'],
         'tot_cas_confirmes_ehpad':['total cumulé du nombre de cas positifs en EHPAD'],
         'tot_cas_possibles_ehpad':['tot_cas_possibles_ehpad:FILLIT'],
         'tot_deces_ehpad':['total cumulé du nombre de décès en EHPAD'],
         'cur_reanimation':['cur_hospitalises: nombre de personnes en reanimation'],
         'cur_hospitalises':['cur_hospitalises: nombre de personnes en hospitalisation'],
         'tot_gueris':['total cumulé du nombre de gueris'],
         'tot_nouvelles_hospitalisations':['tot_nouvelles_hospitalisations: total cumulé du nombre d\'hospitalisation'],
         'tot_nouvelles_reanimations':['tot_nouvelles_reanimations: tot_nouvelles_reanimations: total cumulé du nombre réanimations'],
         'tot_depistes':['tot_depistes: total cumulé du nombre de personnes dépistées (testées par PCR)']
          }
        for k,v in op19nat.items():
              op19nat[k].append('https://raw.githubusercontent.com/opencovid19-fr/data/master/dist/chiffres-cles.csv')
              op19nat[k].append('https://github.com/opencovid19-fr/data')
        mydico = op19nat
    elif namedb == 'owid':
        owid={
        'total_deaths':['total_deaths:FILLIT'],
        'total_cases':['total_cases:FILLIT'],
        'total_tests':['total_tests: FILLIT'],
        'total_vaccinations':['total_vaccinations:FILLIT'],
        'total_cases_per_million':['total_cases_per_million:FILLIT'],
        'total_deaths_per_million':['total_deaths_per_million:FILLIT'],
        'total_vaccinations_per_hundred':['total_vaccinations_per_hundred: COVID19 vaccine doses administered per 100 people'],
        'cur_reproduction_rate':['cur_reproduction_rate:FILLIT'],
        'cur_icu_patients':['cur_icu_patients: (ICU: intensive care unit)'],
        'cur_hosp_patients':['cur_hosp_patients:FILLIT'],
        'cur_idx_positive_rate':['cur_idx_positive_rate:FILLIT']
        }
        for k,v in owid.items():
            owid[k].append("https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv")
            owid[k].append("https://github.com/owid")
        mydico = owid
    elif namedb == 'jhu':
        jhu = {
        'deaths':['deaths: counts include confirmed and probable (where reported).',\
        'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'],
        'confirmed':['confirmed: counts include confirmed and probable (where reported).',\
        'https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'],
        'recovered':['recovered: cases are estimates based on local media reports, and state and local reporting when available, and therefore may be substantially lower than the true number. US state-level recovered cases are from COVID Tracking Project (https://covidtracking.com/)',\
        'https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv']
         }
        for k,v in jhu.items():
             jhu[k].append("https://github.com/CSSEGISandData/COVID-19")
        mydico = jhu
    elif namedb == 'jhu-usa':
        jhuusa = {
        'deaths':['deaths: counts include confirmed and probable (where reported).',\
        'https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv'],
        'confirmed':['confirmed: counts include confirmed and probable (where reported).',\
        'https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv']
        }
        for k,v in jhuusa.items():
            jhuusa[k].append("https://github.com/CSSEGISandData/COVID-19")
        mydico = jhuusa
    elif namedb == 'covid19india':
        india = {
        'Deceased':'Deceased:FILLIT',
        'Confirmed':'Confirmed:FILLIT',
        'Recovered':'Recovered:FILLIT',
        'Tested':'Tested:FILLIT'
        }
        for k,v in india.items():
            india[k].append('https://api.covid19india.org/csv/latest/states.csv')
            india[k].append('https://www.covid19india.org/')
        mydico = india
    elif namedb == 'dpc':
        ita = {
        'tot_casi':['tot_casi:FILLIT','https://github.com/pcm-dpc/COVID-19/raw/master/dati-province/dpc-covid19-ita-province.csv']
        }
        for k,v in ita.items():
            ita[k].append('https://github.com/pcm-dpc/COVID-19')
        mydico = ita
    elif namedb == 'rki':
        rki = {
        'deaths':['deaths:FILLIT','https://github.com/jgehrcke/covid-19-germany-gae/raw/master/deaths-rki-by-ags.csv'],
        'cases':['cases:FILLIT','https://github.com/jgehrcke/covid-19-germany-gae/raw/master/deaths-rki-by-ags.csv'],
        }
        for k,v in rki.items():
            rki[k].append('https://github.com/jgehrcke/covid-19-germany-gae')
        mydico = rki
    else:
        raise CoaKeyError('Error in the database selected, please check !')
    if keys not in mydico:
        raise CoaKeyError(keys + ': this keyword doesn\'t exist for this database !')
    else:
        return mydico[keys]