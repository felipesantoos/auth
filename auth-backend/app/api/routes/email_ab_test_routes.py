"""
Email A/B Test Routes
API endpoints for email A/B testing

Following Hexagonal Architecture:
- Routes depend only on PRIMARY PORTS (interfaces)
- No direct dependency on infrastructure layer
- Services injected via DI container
"""
import logging
from fastapi import APIRouter, Depends, HTTPException

from core.interfaces.primary.email_ab_test_service_interface import IEmailABTestService
from app.api.dicontainer.dicontainer import get_email_ab_test_service
from app.api.dtos.request.email_ab_test_request import (
    CreateABTestRequest,
    AddVariantRequest,
    SendABTestCampaignRequest,
    DeclareWinnerRequest,
)
from app.api.dtos.response.email_ab_test_response import (
    CreateABTestResponse,
    AddVariantResponse,
    ABTestResponse,
    SendABTestCampaignResponse,
    CalculateWinnerResponse,
    DeclareWinnerResponse,
    StopTestResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email/ab-test", tags=["email-ab-testing"])


@router.post("", response_model=CreateABTestResponse)
async def create_ab_test(
    request: CreateABTestRequest,
    ab_test_service: IEmailABTestService = Depends(get_email_ab_test_service)
) -> CreateABTestResponse:
    """
    Create new A/B test.
    
    Args:
        request: Create A/B test request
        ab_test_service: Injected A/B test service
        
    Returns:
        Created test data
    """
    try:
        result = await ab_test_service.create_test(
            name=request.name,
            description=request.description,
            variant_count=request.variant_count,
            min_sample_size=request.min_sample_size,
            confidence_level=request.confidence_level
        )
        
        return CreateABTestResponse(**result)
    
    except Exception as e:
        logger.error(f"Error creating A/B test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create A/B test")


@router.post("/{test_id}/variant", response_model=AddVariantResponse)
async def add_variant(
    test_id: str,
    request: AddVariantRequest,
    ab_test_service: IEmailABTestService = Depends(get_email_ab_test_service)
) -> AddVariantResponse:
    """
    Add variant to A/B test.
    
    Args:
        test_id: A/B test ID
        request: Add variant request
        ab_test_service: Injected A/B test service
        
    Returns:
        Created variant data
    """
    try:
        result = await ab_test_service.add_variant(
            test_id=test_id,
            variant_name=request.variant_name,
            template_name=request.template_name,
            subject_template=request.subject_template,
            weight=request.weight,
            context=request.context
        )
        
        return AddVariantResponse(**result)
    
    except Exception as e:
        logger.error(f"Error adding variant: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add variant")


@router.post("/{test_id}/start")
async def start_test(
    test_id: str,
    ab_test_service: IEmailABTestService = Depends(get_email_ab_test_service)
):
    """
    Start A/B test.
    
    Args:
        test_id: A/B test ID
        ab_test_service: Injected A/B test service
        
    Returns:
        Success message
    """
    try:
        success = await ab_test_service.start_test(test_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="A/B test not found")
        
        return {"status": "started", "test_id": test_id}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start test")


@router.get("/{test_id}", response_model=ABTestResponse)
async def get_test_results(
    test_id: str,
    ab_test_service: IEmailABTestService = Depends(get_email_ab_test_service)
) -> ABTestResponse:
    """
    Get A/B test results and statistics.
    
    Args:
        test_id: A/B test ID
        ab_test_service: Injected A/B test service
        
    Returns:
        Test results with variant metrics
    """
    try:
        results = await ab_test_service.get_test_results(test_id)
        
        if not results:
            raise HTTPException(status_code=404, detail="A/B test not found")
        
        return ABTestResponse(**results)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting test results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get test results")


@router.post("/{test_id}/send", response_model=SendABTestCampaignResponse)
async def send_ab_test_campaign(
    test_id: str,
    request: SendABTestCampaignRequest,
    ab_test_service: IEmailABTestService = Depends(get_email_ab_test_service)
) -> SendABTestCampaignResponse:
    """
    Send A/B test campaign to recipients.
    
    Args:
        test_id: A/B test ID
        request: Campaign send request
        ab_test_service: Injected A/B test service
        
    Returns:
        Campaign send results
    """
    try:
        results = await ab_test_service.send_ab_test_email(
            test_id=test_id,
            recipients=request.recipients,
            base_context=request.base_context
        )
        
        successful = sum(1 for r in results if r.get('success'))
        failed = len(results) - successful
        
        variants_used = list(set(r['variant'] for r in results if 'variant' in r))
        
        return SendABTestCampaignResponse(
            total_sent=len(results),
            successful=successful,
            failed=failed,
            variants_used=variants_used
        )
    
    except Exception as e:
        logger.error(f"Error sending A/B test campaign: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to send campaign")


@router.get("/{test_id}/winner", response_model=CalculateWinnerResponse)
async def calculate_winner(
    test_id: str,
    metric: str = "open_rate",
    ab_test_service: IEmailABTestService = Depends(get_email_ab_test_service)
) -> CalculateWinnerResponse:
    """
    Calculate A/B test winner.
    
    Args:
        test_id: A/B test ID
        metric: Metric to compare (open_rate, click_rate, ctr)
        ab_test_service: Injected A/B test service
        
    Returns:
        Winner variant data
    """
    try:
        winner = await ab_test_service.calculate_winner(test_id, metric)
        
        if not winner:
            raise HTTPException(
                status_code=400,
                detail="Not enough data or no statistically significant winner yet"
            )
        
        return CalculateWinnerResponse(**winner)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating winner: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate winner")


@router.post("/{test_id}/winner", response_model=DeclareWinnerResponse)
async def declare_winner(
    test_id: str,
    request: DeclareWinnerRequest,
    ab_test_service: IEmailABTestService = Depends(get_email_ab_test_service)
) -> DeclareWinnerResponse:
    """
    Manually declare A/B test winner.
    
    Args:
        test_id: A/B test ID
        request: Declare winner request
        ab_test_service: Injected A/B test service
        
    Returns:
        Winner declaration confirmation
    """
    try:
        success = await ab_test_service.declare_winner(test_id, request.variant_name)
        
        if not success:
            raise HTTPException(status_code=404, detail="A/B test not found")
        
        return DeclareWinnerResponse(
            status="winner_declared",
            test_id=test_id,
            winner_variant=request.variant_name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error declaring winner: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to declare winner")


@router.delete("/{test_id}", response_model=StopTestResponse)
async def stop_test(
    test_id: str,
    ab_test_service: IEmailABTestService = Depends(get_email_ab_test_service)
) -> StopTestResponse:
    """
    Stop A/B test.
    
    Args:
        test_id: A/B test ID
        ab_test_service: Injected A/B test service
        
    Returns:
        Stop confirmation
    """
    try:
        success = await ab_test_service.stop_test(test_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="A/B test not found")
        
        from datetime import datetime
        return StopTestResponse(
            status="stopped",
            test_id=test_id,
            end_date=datetime.utcnow().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to stop test")

