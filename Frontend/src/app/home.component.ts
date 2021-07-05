import { Component } from '@angular/core';
import { AuthService } from './auth.service';

@Component({
    selector: 'home',
    templateUrl: './home.component.html'
})
export class HomeComponent {
    constructor(private authService: AuthService) {}
    
    profileJson: string = null;
    
    ngOnInIt(){
        this.authService.userProfile$.subscribe(
            (profile) => (this.profileJson = JSON.stringify(profile, null, 2))
        );
    }
}