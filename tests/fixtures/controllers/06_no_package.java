import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;

@Controller
@RequestMapping("/test")
public class NoPackageController {

    @Autowired
    private TestService testService;

    @GetMapping("/hello")
    public String hello() {
        return "hello";
    }

    @PostMapping("/submit")
    public String submit(@RequestParam("data") String data) {
        testService.process(data);
        return "success";
    }
}
