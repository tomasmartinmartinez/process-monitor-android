package com.example.processmonitor.service

import com.example.processmonitor.model.ProcessInfo
import java.io.File

class ProcessMonitor {

    private var prevProcCpu: Map<Int, Long> = emptyMap()
    private var prevTotalCpu: Long = 0L
    private val clockTicksPerSec: Long = 100L

    val numCores: Int = Runtime.getRuntime().availableProcessors()

    fun snapshot(): List<ProcessInfo> {
        val procDir = File("/proc")
        val pidDirs = procDir.listFiles { f ->
            f.isDirectory && f.name.matches(Regex("^\\d+$"))
        } ?: return emptyList()

        val currentProcCpu = mutableMapOf<Int, Long>()
        val currentTotalCpu = readTotalCpuTime()
        val results = mutableListOf<ProcessInfo>()

        for (pidDir in pidDirs) {
            val pid = pidDir.name.toInt()
            try {
                val stat = readProcStat(pid) ?: continue
                currentProcCpu[pid] = stat.totalCpuTime

                val prevProc = prevProcCpu[pid] ?: 0L
                val deltaProc = stat.totalCpuTime - prevProc
                val deltaTotal = currentTotalCpu - prevTotalCpu

                val cpuPercent = if (deltaTotal > 0) {
                    (deltaProc.toFloat() / deltaTotal.toFloat()) * 100f * numCores
                } else 0f

                results.add(
                    ProcessInfo(
                        pid = pid,
                        name = stat.comm,
                        user = getUserName(stat.uid),
                        cpuPercent = cpuPercent,
                        memKb = readProcMem(pid),
                        state = stat.state,
                        threads = stat.numThreads
                    )
                )
            } catch (_: Exception) { }
        }

        prevProcCpu = currentProcCpu
        prevTotalCpu = currentTotalCpu
        return results
    }

    private data class StatInfo(
        val comm: String,
        val state: String,
        val totalCpuTime: Long,
        val numThreads: Int,
        val uid: Int
    )

    private fun readProcStat(pid: Int): StatInfo? {
        val statFile = File("/proc/$pid/stat")
        val text = statFile.readText()

        val openParen = text.indexOf('(')
        val closeParen = text.lastIndexOf(')')
        if (openParen < 0 || closeParen < 0) return null

        val comm = text.substring(openParen + 1, closeParen)
        val rest = text.substring(closeParen + 2).trim().split(Regex("\\s+"))

        if (rest.size < 13) return null
        val state = rest[0]
        val utime = rest[11].toLongOrNull() ?: 0L
        val stime = rest[12].toLongOrNull() ?: 0L
        val numThreads = if (rest.size > 19) rest[19].toIntOrNull() ?: 1 else 1
        val uid = readProcUid(pid)
        return StatInfo(comm, state, utime + stime, numThreads, uid)
    }

    private fun readProcUid(pid: Int): Int {
        return try {
            File("/proc/$pid/status").useLines { lines ->
                lines.firstOrNull { it.startsWith("Uid:") }
                    ?.split(Regex("\\s+"))
                    ?.getOrNull(2)
                    ?.toIntOrNull() ?: -1
            }
        } catch (_: Exception) { -1 }
    }

    private fun readProcMem(pid: Int): Long {
        return try {
            val statm = File("/proc/$pid/statm").readText().trim().split(Regex("\\s+"))
            val residentPages = statm.getOrNull(1)?.toLongOrNull() ?: 0L
            residentPages * 4L
        } catch (_: Exception) { 0L }
    }

    private fun readTotalCpuTime(): Long {
        return try {
            File("/proc/stat").useLines { lines ->
                val cpuLine = lines.firstOrNull { it.startsWith("cpu ") } ?: return 0L
                cpuLine.split(Regex("\\s+"))
                    .drop(1)
                    .mapNotNull { it.toLongOrNull() }
                    .sum()
            }
        } catch (_: Exception) { 0L }
    }

    private val uidCache = mutableMapOf<Int, String>()

    private fun getUserName(uid: Int): String {
        return uidCache.getOrPut(uid) {
            when (uid) {
                0 -> "root"
                1000 -> "system"
                in 10000..19999 -> "u0_a${uid - 10000}"
                else -> "uid=$uid"
            }
        }
    }
}
