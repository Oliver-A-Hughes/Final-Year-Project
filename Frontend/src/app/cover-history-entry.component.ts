import { Component } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { BackendService } from './backendService';

@Component({
    selector: 'coverhistory',
    templateUrl: './cover-history-entry.component.html'
})
export class CoverHistoryEntryComponent {
    
    constructor(private backendService: BackendService,
        private route: ActivatedRoute) {}

    cancelRequest = false;

    ngOnInit(){
        this.backendService.coverRequestRefreshNeeded
            .subscribe(() => {
               this.backendService.getCoverRequest(this.route.snapshot.params.id);
            });
        this.backendService.getCoverRequest(this.route.snapshot.params.id); 
    }

    cancelRequestButtonClicked(){
        this.cancelRequest = true
        this.ngOnInit()
    }

    confrimCancellation(){
        this.backendService.cancelCoverRequest(this.route.snapshot.params.id);
        this.ngOnInit();
    }

    abortCancellation(){
        this.cancelRequest = false
        this.ngOnInit
    }
}