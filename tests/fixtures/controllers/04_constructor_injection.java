package com.example.legacy;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;
import com.example.service.LegacyService;
import com.example.service.AuditService;

@Controller
public class LegacyController {

    private final LegacyService legacyService;
    private final AuditService auditService;

    @Autowired
    public LegacyController(LegacyService legacyService, AuditService auditService) {
        this.legacyService = legacyService;
        this.auditService = auditService;
    }

    @RequestMapping(value = "/legacy/action", method = RequestMethod.POST)
    public String handleAction(@RequestParam("action") String action) {
        legacyService.process(action);
        auditService.log("Action processed: " + action);
        return "redirect:/legacy/result";
    }

    @RequestMapping(value = "/legacy/view/{id}", method = RequestMethod.GET)
    public String viewItem(@PathVariable("id") Long itemId) {
        return "legacy/view";
    }
}
