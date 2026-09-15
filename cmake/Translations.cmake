# Languages with 0% progress or low progress and alternatives are disabled
set(TS_FILES
#   translations/am/butter_am_ET.ts
    translations/ar/butter_ar_SA.ts
    translations/bn/butter_bn_BD.ts
    translations/ca/butter_ca_ES.ts
    translations/de/butter_de_DE.ts
    translations/es-ES/butter_es_ES.ts
    translations/fa/butter_fa_IR.ts
    translations/fi/butter_fi_FI.ts
#   translations/fil/butter_fil_PH.ts
    translations/fr/butter_fr_FR.ts
    translations/he/butter_he_IL.ts
    translations/hi/butter_hi_IN.ts
    translations/it/butter_it_IT.ts
    translations/ja/butter_ja_JP.ts
#   translations/km/butter_km_KH.ts
    translations/ko/butter_ko_KR.ts
    translations/nl/butter_nl_NL.ts
#   translations/pa-IN/butter_pa_IN.ts
    translations/pl/butter_pl_PL.ts
#   translations/pt-BR/butter_pt_BR.ts
    translations/pt-PT/butter_pt_PT.ts
    translations/ro/butter_ro_RO.ts
    translations/ru/butter_ru_RU.ts
#   translations/sv-SE/butter_sv_SE.ts
#   translations/sw/butter_sw_KE.ts
#   translations/th/butter_th_TH.ts
    translations/tr/butter_tr_TR.ts
    translations/uk/butter_uk_UA.ts
#   translations/ur-IN/butter_ur_IN.ts
    translations/ur-PK/butter_ur_PK.ts
    translations/vi/butter_vi_VN.ts
    translations/zh-CN/butter_zh_CN.ts
    translations/zh-TW/butter_zh_TW.ts
)

set_source_files_properties(${TS_FILES} PROPERTIES OUTPUT_LOCATION ${CMAKE_CURRENT_BINARY_DIR}/translations)
if (BUTTER_QT EQUAL 6)
    find_package(Qt6LinguistTools REQUIRED)
    qt6_add_translation(qmFiles ${TS_FILES})
elseif(BUTTER_QT EQUAL 5)
    find_package(Qt5LinguistTools REQUIRED)
    qt5_add_translation(qmFiles ${TS_FILES})
endif()
add_custom_target(translations ALL DEPENDS ${qmFiles} SOURCES ${TS_FILES})

install(FILES
    ${qmFiles}
    # For Linux it might be more correct to use ${MAKE_INSTALL_LOCALEDIR}, but that
    # uses share/locale_name/software_name layout instead of share/software_name/locale_files.
    DESTINATION ${BUTTER_INSTALL_DATADIR}/translations
)

