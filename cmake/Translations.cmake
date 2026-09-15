# Languages with 0% progress or low progress and alternatives are disabled
set(TS_FILES
#   translations/am/clutter_am_ET.ts
    translations/ar/clutter_ar_SA.ts
    translations/bn/clutter_bn_BD.ts
    translations/ca/clutter_ca_ES.ts
    translations/de/clutter_de_DE.ts
    translations/es-ES/clutter_es_ES.ts
    translations/fa/clutter_fa_IR.ts
    translations/fi/clutter_fi_FI.ts
#   translations/fil/clutter_fil_PH.ts
    translations/fr/clutter_fr_FR.ts
    translations/he/clutter_he_IL.ts
    translations/hi/clutter_hi_IN.ts
    translations/it/clutter_it_IT.ts
    translations/ja/clutter_ja_JP.ts
#   translations/km/clutter_km_KH.ts
    translations/ko/clutter_ko_KR.ts
    translations/nl/clutter_nl_NL.ts
#   translations/pa-IN/clutter_pa_IN.ts
    translations/pl/clutter_pl_PL.ts
#   translations/pt-BR/clutter_pt_BR.ts
    translations/pt-PT/clutter_pt_PT.ts
    translations/ro/clutter_ro_RO.ts
    translations/ru/clutter_ru_RU.ts
#   translations/sv-SE/clutter_sv_SE.ts
#   translations/sw/clutter_sw_KE.ts
#   translations/th/clutter_th_TH.ts
    translations/tr/clutter_tr_TR.ts
    translations/uk/clutter_uk_UA.ts
#   translations/ur-IN/clutter_ur_IN.ts
    translations/ur-PK/clutter_ur_PK.ts
    translations/vi/clutter_vi_VN.ts
    translations/zh-CN/clutter_zh_CN.ts
    translations/zh-TW/clutter_zh_TW.ts
)

set_source_files_properties(${TS_FILES} PROPERTIES OUTPUT_LOCATION ${CMAKE_CURRENT_BINARY_DIR}/translations)
if (CLUTTER_QT EQUAL 6)
    find_package(Qt6LinguistTools REQUIRED)
    qt6_add_translation(qmFiles ${TS_FILES})
elseif(CLUTTER_QT EQUAL 5)
    find_package(Qt5LinguistTools REQUIRED)
    qt5_add_translation(qmFiles ${TS_FILES})
endif()
add_custom_target(translations ALL DEPENDS ${qmFiles} SOURCES ${TS_FILES})

install(FILES
    ${qmFiles}
    # For Linux it might be more correct to use ${MAKE_INSTALL_LOCALEDIR}, but that
    # uses share/locale_name/software_name layout instead of share/software_name/locale_files.
    DESTINATION ${CLUTTER_INSTALL_DATADIR}/translations
)

