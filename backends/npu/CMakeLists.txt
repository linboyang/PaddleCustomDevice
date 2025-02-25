cmake_minimum_required(VERSION 3.10)

project(paddle-custom-npu CXX C)
set(CUSTOM_NPU_NAME "paddle-custom-npu")

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/cmake")

include(paddle)
include(version)
include(generic)
include(external/ascend)
include_directories(${CMAKE_SOURCE_DIR})

option(WITH_MKLDNN "compile with MKLDNN support" ON)
option(WITH_KERNELS "compile with custom kernels" ON)
option(WITH_TESTING "compile with unit testing" OFF)
option(WITH_ARM "compile with arm support" OFF)
option(WITH_ASCEND_TRANSFORMER_ACC "compile with ascend transformer acceleration" OFF)
option(ON_INFER "compile with inference c++ lib" OFF)
option(ON_INFER "compile with inference c++ lib" OFF)

message(STATUS "CXX compiler: ${CMAKE_CXX_COMPILER}, version: "
               "${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")
message(STATUS "C compiler: ${CMAKE_C_COMPILER}, version: "
               "${CMAKE_C_COMPILER_ID} ${CMAKE_C_COMPILER_VERSION}")
message(STATUS "AR tools: ${CMAKE_AR}")
set(CMAKE_CXX_FLAGS
    "${CMAKE_CXX_FLAGS} -Wno-narrowing -Wno-terminate -Wno-write-strings -Wno-return-type"
)

# custom runtime
set(CUSTOM_NPU_SRCS runtime/runtime.cc)
add_definitions(-DPADDLE_WITH_CUSTOM_DEVICE)
# TODO(qiil93): avoid compile error, to be removed
add_definitions(-DPADDLE_WITH_CUSTOM_KERNEL)
if(WITH_ARM)
  add_definitions(-DPADDLE_WITH_ARM)
endif()

# custom kernels
if(WITH_KERNELS)
  file(
    GLOB_RECURSE CUSTOM_KERNEL_SRCS
    RELATIVE ${CMAKE_SOURCE_DIR}
    kernels/*.cc)
  list(APPEND CUSTOM_NPU_SRCS ${CUSTOM_KERNEL_SRCS})

  file(
    GLOB_RECURSE CUSTOM_CUSTOM_OP_SRCS
    RELATIVE ${CMAKE_SOURCE_DIR}
    custom_op/*.cc)
  list(APPEND CUSTOM_NPU_SRCS ${CUSTOM_CUSTOM_OP_SRCS})

  if(WITH_ASCEND_TRANSFORMER_ACC)
    file(
      GLOB_RECURSE CUSTOM_ACC_RUNNER_SRCS
      RELATIVE ${CMAKE_SOURCE_DIR}
      custom_op/self_attention/*.cpp
      custom_op/self_attention_kv_cache_fusion_gpt3/*.cpp)
    list(APPEND CUSTOM_NPU_SRCS ${CUSTOM_ACC_RUNNER_SRCS})
  endif()
endif()

# ASCEND TRANSFORMER ACCELERATION
if(WITH_ASCEND_TRANSFORMER_ACC)
  add_definitions(-DPADDLE_WITH_ASCEND_TRANSFORMER_ACC)
endif()

# C++ infer lib need to compatiable with CXX11
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D_GLIBCXX_USE_CXX11_ABI=1")
if(ON_INFER)
  link_directories(${PADDLE_INFERENCE_LIB_DIR})
endif()

# build shared library
add_library(${CUSTOM_NPU_NAME} SHARED ${CUSTOM_NPU_SRCS})
add_dependencies(${CUSTOM_NPU_NAME} ascend_cl)
target_link_libraries(${CUSTOM_NPU_NAME} PRIVATE ${ascendcl_lib}
                                                 ${ascend_hccl_lib} glog gflags)
target_link_libraries(${CUSTOM_NPU_NAME} PRIVATE ${acl_op_compiler_lib})

if(WITH_ASCEND_TRANSFORMER_ACC)
  target_link_libraries(${CUSTOM_NPU_NAME} PRIVATE $ENV{ACLTRANSFORMER_HOME_PATH}/lib/libacltransformer.so)
  include_directories($ENV{ACLTRANSFORMER_HOME_PATH}/include)
endif()

# link paddle shared library
include(third_party)
add_dependencies(${CUSTOM_NPU_NAME} third_party)
if(ON_INFER)
  target_link_libraries(${CUSTOM_NPU_NAME} PRIVATE paddle_inference)
  target_compile_definitions(${CUSTOM_NPU_NAME} PRIVATE PADDLE_ON_INFERENCE)
else()
  target_link_libraries(${CUSTOM_NPU_NAME} PRIVATE ${PADDLE_CORE_LIB})
  target_link_libraries(${CUSTOM_NPU_NAME} PRIVATE pybind)
  find_package(PythonInterp ${PY_VERSION} REQUIRED)
  find_package(PythonLibs ${PY_VERSION} REQUIRED)
  include_directories(${PYTHON_INCLUDE_DIR})
endif()

# testing
if(WITH_TESTING)
  set(PYTHON_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../python")
  add_subdirectory(tests)
  add_custom_command(
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/tests/.timestamp
    COMMAND cp -r ${CMAKE_SOURCE_DIR}/tests ${CMAKE_CURRENT_BINARY_DIR})
  add_custom_target(python_tests ALL
                    DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/tests/.timestamp)
endif()

# get git commit id
execute_process(
  COMMAND git rev-parse HEAD
  WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
  OUTPUT_VARIABLE GIT_HASH
  OUTPUT_STRIP_TRAILING_WHITESPACE)
message(STATUS "Git commit id is: ${GIT_HASH}")

configure_file(${CMAKE_CURRENT_SOURCE_DIR}/setup.py.in
               ${CMAKE_CURRENT_BINARY_DIR}/setup.py)

# packing wheel package
add_custom_command(
  TARGET ${CUSTOM_NPU_NAME}
  POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E remove -f ${CMAKE_CURRENT_BINARY_DIR}/python/
  COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_CURRENT_BINARY_DIR}/python/
  COMMAND ${CMAKE_COMMAND} -E make_directory
          ${CMAKE_CURRENT_BINARY_DIR}/python/paddle_custom_device/
  COMMAND
    ${CMAKE_COMMAND} -E copy_if_different
    ${CMAKE_CURRENT_BINARY_DIR}/lib${CUSTOM_NPU_NAME}.so
    ${CMAKE_CURRENT_BINARY_DIR}/python/paddle_custom_device/
  COMMENT "Creating custom device dirrectories------>>>")

add_custom_command(
  OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/python/.timestamp
  COMMAND ${CMAKE_COMMAND} -E make_directory
    ${CMAKE_CURRENT_BINARY_DIR}/python/paddle_custom_device/npu/passes
  COMMAND ${CMAKE_COMMAND} -E remove -f
    ${CMAKE_CURRENT_BINARY_DIR}/python/paddle_custom_device/npu/passes    
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
    ${CMAKE_SOURCE_DIR}/passes/*
    ${CMAKE_CURRENT_BINARY_DIR}/python/paddle_custom_device/npu/passes
  COMMAND python3 ${CMAKE_CURRENT_BINARY_DIR}/setup.py bdist_wheel
  DEPENDS ${CUSTOM_NPU_NAME}
  COMMENT "Packing whl packages------>>>")

add_custom_target(python_package ALL
                  DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/python/.timestamp)
