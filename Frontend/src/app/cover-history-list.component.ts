import { Component } from '@angular/core';
import { BackendService } from './backendService';

@Component({
    selector: 'coverhistory',
    templateUrl: './cover-history-list.component.html'
})
export class CoverHistoryListComponent {
    
    constructor(private backendService: BackendService) {}

    ngOnInit(){
        this.backendService.getCoverHistory(); 
    }
}