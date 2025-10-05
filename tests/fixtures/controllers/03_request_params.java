package com.example.web;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.ModelAndView;
import javax.annotation.Resource;
import com.example.service.ProductService;
import com.example.model.Product;
import java.util.List;

@Controller
@RequestMapping("/products")
public class ProductController {

    @Resource
    private ProductService productService;

    @GetMapping("/search")
    public ModelAndView search(
        @RequestParam(value = "keyword", required = false) String keyword,
        @RequestParam(value = "page", defaultValue = "1") int page,
        @RequestParam(value = "size", defaultValue = "20") int size,
        @RequestParam(value = "sortBy", required = false, defaultValue = "name") String sortField
    ) {
        List<Product> products = productService.search(keyword, page, size, sortField);
        ModelAndView mav = new ModelAndView("products/search");
        mav.addObject("products", products);
        return mav;
    }

    @GetMapping("/filter")
    public ModelAndView filter(
        @RequestParam(value = "category") String category,
        @RequestParam(value = "minPrice", required = false) Double minPrice,
        @RequestParam(value = "maxPrice", required = false) Double maxPrice
    ) {
        List<Product> products = productService.filter(category, minPrice, maxPrice);
        return new ModelAndView("products/list").addObject("products", products);
    }
}
