package com.example.api;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.beans.factory.annotation.Autowired;
import com.example.service.DataService;
import com.example.dto.*;
import java.util.*;

@RestController
@RequestMapping("/api/data")
public class DataController {

    @Autowired
    private DataService dataService;

    @GetMapping("/complex")
    public ResponseEntity<Map<String, List<Map<String, Object>>>> getComplexData() {
        Map<String, List<Map<String, Object>>> data = dataService.getComplexData();
        return ResponseEntity.ok(data);
    }

    @PostMapping("/nested")
    public ResponseEntity<List<Map<String, Set<String>>>> processNested(
        @RequestBody Map<String, List<String>> input
    ) {
        List<Map<String, Set<String>>> result = dataService.processNested(input);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/generic/{id}")
    public ResponseEntity<Map<String, ?>> getGeneric(@PathVariable Long id) {
        Map<String, ?> result = dataService.getGeneric(id);
        return ResponseEntity.ok(result);
    }

    @PostMapping("/collection")
    public ResponseEntity<List<? extends BaseDTO>> getCollection(
        @RequestParam("type") String type
    ) {
        List<? extends BaseDTO> results = dataService.getByType(type);
        return ResponseEntity.ok(results);
    }
}
