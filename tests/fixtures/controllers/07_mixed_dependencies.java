package com.example.web;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;
import javax.annotation.Resource;
import com.example.service.*;
import com.example.model.Report;

@Controller
@RequestMapping("/reports")
public class ReportController {

    @Autowired
    private ReportService reportService;

    @Resource
    private ExportService exportService;

    @Autowired
    private NotificationService notificationService;

    private final AuditService auditService;
    private final SecurityService securityService;

    @Autowired
    public ReportController(AuditService auditService, SecurityService securityService) {
        this.auditService = auditService;
        this.securityService = securityService;
    }

    @GetMapping("/generate")
    public String generateReport(
        @RequestParam("type") String reportType,
        @RequestParam(value = "format", defaultValue = "pdf") String format
    ) {
        securityService.checkAccess();
        Report report = reportService.generate(reportType);
        auditService.log("Report generated: " + reportType);
        return "reports/view";
    }

    @PostMapping("/export")
    public String exportReport(@RequestBody Report report) {
        exportService.export(report);
        notificationService.notify("Export completed");
        return "redirect:/reports/list";
    }
}
