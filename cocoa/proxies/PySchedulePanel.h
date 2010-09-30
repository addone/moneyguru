/* 
Copyright 2010 Hardcoded Software (http://www.hardcoded.net)

This software is licensed under the "BSD" License as described in the "LICENSE" file, 
which should be included with this package. The terms are also available at 
http://www.hardcoded.net/licenses/bsd_license
*/

#import <Cocoa/Cocoa.h>
#import "PyPanelWithTransaction.h"

@interface PySchedulePanel : PyPanelWithTransaction {}
- (NSString *)startDate;
- (void)setStartDate:(NSString *)startDate;
- (NSString *)stopDate;
- (void)setStopDate:(NSString *)stopDate;
- (void)setCheckno:(NSString *)checkno;
- (NSInteger)repeatEvery;
- (void)setRepeatEvery:(NSInteger)value;
- (NSString *)repeatEveryDesc;
- (NSInteger)repeatTypeIndex;
- (void)setRepeatTypeIndex:(NSInteger)value;
- (NSArray *)repeatOptions;
@end