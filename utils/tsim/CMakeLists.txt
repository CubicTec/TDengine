aux_source_directory(src TSIM_SRC)
add_executable(tsim ${TSIM_SRC})
target_link_libraries(
    tsim
    PUBLIC util
    PUBLIC common
    PUBLIC os
    PUBLIC cjson
)

if (${BUILD_SLIM})
  target_link_libraries(tsim PUBLIC taos)
else ()
  target_link_libraries(tsim PUBLIC taos_static)
endif ()

target_include_directories(
    tsim
    PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/inc"
)
