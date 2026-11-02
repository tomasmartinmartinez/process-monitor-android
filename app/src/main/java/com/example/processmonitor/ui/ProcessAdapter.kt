package com.example.processmonitor.ui

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.example.processmonitor.databinding.ItemProcessBinding
import com.example.processmonitor.model.ProcessInfo
import java.util.Locale

class ProcessAdapter :
    ListAdapter<ProcessInfo, ProcessAdapter.ProcessVH>(DIFF) {

    companion object {
        val DIFF = object : DiffUtil.ItemCallback<ProcessInfo>() {
            override fun areItemsTheSame(a: ProcessInfo, b: ProcessInfo) = a.pid == b.pid
            override fun areContentsTheSame(a: ProcessInfo, b: ProcessInfo) = a == b
        }
    }

    class ProcessVH(val binding: ItemProcessBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ProcessVH {
        val binding = ItemProcessBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return ProcessVH(binding)
    }

    override fun onBindViewHolder(holder: ProcessVH, position: Int) {
        val p = getItem(position)
        with(holder.binding) {
            txtPid.text = p.pid.toString()
            txtName.text = p.name
            txtUser.text = p.user
            txtState.text = p.state
            txtThreads.text = "${p.threads} h"
            txtCpu.text = String.format(Locale.US, "%5.1f%%", p.cpuPercent)
            txtMem.text = formatMem(p.memKb)

            txtCpu.setTextColor(
                when {
                    p.cpuPercent > 50 -> 0xFFE53935.toInt()
                    p.cpuPercent > 20 -> 0xFFFB8C00.toInt()
                    p.cpuPercent > 5  -> 0xFFFDD835.toInt()
                    else              -> 0xFF43A047.toInt()
                }
            )
        }
    }

    private fun formatMem(kb: Long): String = when {
        kb < 1024 -> "${kb} KB"
        kb < 1024 * 1024 -> String.format(Locale.US, "%.1f MB", kb / 1024.0)
        else -> String.format(Locale.US, "%.2f GB", kb / (1024.0 * 1024.0))
    }
}
