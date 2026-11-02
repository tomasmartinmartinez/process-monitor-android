package com.example.processmonitor.model

data class ProcessInfo(
    val pid: Int,
    val name: String,
    val user: String,
    val cpuPercent: Float,
    val memKb: Long,
    val state: String,
    val threads: Int
)
