// #500 point 6: our own profiling names. `stat CastleDefender` in the console shows them; Unreal Insights (trace cpu) shows the same scopes by name.
#pragma once

#include "Stats/Stats.h"
#include "ProfilingDebugging/CpuProfilerTrace.h"

DECLARE_STATS_GROUP(TEXT("CastleDefender"), STATGROUP_CastleDefender, STATCAT_Advanced);

// One line per scope: a stat counter for `stat CastleDefender` + a named Insights event.
#define CD_SCOPE(StatName) \
	SCOPE_CYCLE_COUNTER(StatName); \
	TRACE_CPUPROFILER_EVENT_SCOPE(StatName)
