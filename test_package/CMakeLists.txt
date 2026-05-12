cmake_minimum_required(VERSION 3.15)
project(PackageTest CXX)

find_package(cpptango CONFIG REQUIRED)

add_executable(tango_package_test tango_package_test.cpp)
target_link_libraries(tango_package_test PUBLIC cpptango::cpptango)
