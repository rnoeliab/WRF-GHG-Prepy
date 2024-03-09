#!/bin/bash

cd ../input/anthr_ghg/EDGAR/
mkdir data_ghg
cd data_ghg

mkdir data_co
cd data_co
for i in {AWB,CHE,ENE,FFF,FOO_PAP,IND,IRO,NFE,NMM,PRO,RCO,REF_TRF,SWD_INC,TNR_Aviation_CDS,TNR_Aviation_CRS,TNR_Aviation_LTO,TNR_Other,TNR_Ship,TRO_noRES}
do
mkdir $i
cd $i
URLS="http://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v61_AP/CO/$i/EDGARv6.1_CO_2018_monthly_$i""_nc.zip"
for u in $URLS
do
wget "$u"
done
unzip *zip
rm *zip
cd ..
done
cd ..

mkdir data_co2_excl
cd data_co2_excl
for i in {AGS,CHE,ENE,FFF,IND,IRO,NFE,NMM,PRO,RCO,REF_TRF,SWD_INC,TNR_Aviation_CDS,TNR_Aviation_CRS,TNR_Aviation_LTO,TNR_Other,TNR_Ship,TRO_noRES} 
do
mkdir $i
cd $i
URLS="http://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v60_GHG/CO2_excl_short-cycle_org_C/$i/v6.0_CO2_excl_short-cycle_org_C_2018_monthly_$i""_nc.zip"
for u in $URLS
do
wget "$u"
done
unzip *zip
rm *zip
cd ..
done
cd ..

mkdir data_co2_org
cd data_co2_org
for i in {AWB,ENE,IND,RCO,REF_TRF,SWD_INC,TNR_Other,TNR_Ship,TRO_noRES} 
do
mkdir $i
cd $i
URLS="http://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v60_GHG/CO2_org_short-cycle_C/$i/v6.0_CO2_org_short-cycle_C_2018_monthly_$i""_nc.zip"
for u in $URLS
do
wget "$u"
done
unzip *zip
rm *zip
cd ..
done
cd ..

mkdir data_ch4
cd data_ch4
for i in {ENE,REF_TRF,IND,RCO,PRO_COAL,PRO,PRO_OIL,PRO_GAS,TRO_noRES,TNR_Other,TNR_Aviation_CDS,TNR_Aviation_CRS,TNR_Aviation_LTO,TNR_Ship,CHE,IRO,ENF,MNM,AWB,AGS,SWD_LDF,SWD_INC,WWT,FFF}
do
mkdir $i
cd $i
URLS="http://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/EDGAR/datasets/v60_GHG/CH4/$i/v6.0_CH4_2018_monthly_$i""_nc.zip"
for u in $URLS
do
wget "$u"
done
unzip *zip
rm *zip
cd ..
done

rm *html