#pragma once

//#ifdef CRS_WRAPPER_EXPORT
//#define CRS_WRAPPER_API __declspec(dllexport)
//#else
//#define CRS_WRAPPER_API __declspec(dllimport)
//#endif

void crsInitDll();

extern "C" __declspec(dllexport) void* crsPipeWrapper(int fnId);
