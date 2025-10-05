package com.example.api;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.beans.factory.annotation.Autowired;
import com.example.service.OrderService;
import com.example.dto.OrderRequest;
import javax.validation.Valid;
import java.util.Map;

@RestController
@RequestMapping("/api/orders")
public class OrderController {

    @Autowired
    private OrderService orderService;

    @GetMapping("/{orderId}/items/{itemId}")
    public ResponseEntity<Map<String, Object>> getOrderItem(
        @PathVariable("orderId") Long orderId,
        @PathVariable("itemId") Long itemId
    ) {
        Map<String, Object> result = orderService.getOrderItem(orderId, itemId);
        return ResponseEntity.ok(result);
    }

    @PostMapping("/{id}/validate")
    public ResponseEntity<Void> validateOrder(
        @PathVariable Long id,
        @Valid @RequestBody OrderRequest request
    ) {
        orderService.validate(id, request);
        return ResponseEntity.noContent().build();
    }

    @PutMapping("/{orderId}/items/{itemId}/quantity")
    public ResponseEntity<Map<String, String>> updateQuantity(
        @PathVariable Long orderId,
        @PathVariable Long itemId,
        @RequestParam("quantity") Integer quantity
    ) {
        Map<String, String> result = orderService.updateQuantity(orderId, itemId, quantity);
        return ResponseEntity.ok(result);
    }
}
