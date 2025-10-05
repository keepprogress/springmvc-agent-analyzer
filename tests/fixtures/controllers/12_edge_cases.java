package com.example.api.v2;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpHeaders;
import javax.annotation.Resource;
import com.example.service.EdgeCaseService;
import java.util.*;

@RestController
@RequestMapping("/api/v2/edge")
public class EdgeCaseController {

    @Resource(name = "edgeCaseService")
    private EdgeCaseService edgeCaseService;

    @GetMapping("/wildcard")
    public ResponseEntity<List<?>> getWildcard() {
        List<?> result = edgeCaseService.getWildcard();
        return ResponseEntity.ok(result);
    }

    @PostMapping("/headers")
    public ResponseEntity<Map<String, Object>> withHeaders(
        @RequestHeader("X-Custom-Header") String customHeader,
        @RequestHeader(value = "Authorization", required = false) String auth,
        @RequestBody Map<String, ?> body
    ) {
        Map<String, Object> result = edgeCaseService.processWithHeaders(customHeader, auth, body);
        return ResponseEntity.ok(result);
    }

    @RequestMapping(value = "/multi", method = {RequestMethod.GET, RequestMethod.POST})
    public ResponseEntity<String> multiMethod(
        @RequestParam(required = false) String param
    ) {
        return ResponseEntity.ok(edgeCaseService.handleMulti(param));
    }

    @GetMapping("/matrix/{id}")
    public ResponseEntity<Object> matrixParams(
        @PathVariable Long id,
        @MatrixVariable(required = false) String filter
    ) {
        Object result = edgeCaseService.processMatrix(id, filter);
        return ResponseEntity.ok(result);
    }
}
